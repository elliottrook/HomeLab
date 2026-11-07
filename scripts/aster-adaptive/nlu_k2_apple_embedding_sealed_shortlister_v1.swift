import CryptoKit
import Darwin
import Foundation
import NaturalLanguage

let corpusSHA256 = "9e2dd321c6660ad4bd09e9824c24b9727a30eba60a8df37e09f17d436ccce90a"
let evaluationSHA256 = "78f7b8aa7b8f8202e38333be4d497a489c1f36b3c6209839c05ecd3975191cae"
let manifestSHA256 = "2abcd02371b087ebc6db95b04dd271b518624cd063ffeb4612341bcb4c1b97ee"
let ontologySHA256 = "aa603ab746a1250c8f2089b54e1a3e5b29fc3d01cb3c988bacc198a968bbea44"

struct CorpusCase: Decodable {
    let id: String
    let split: String
    let text: String
    let label_id: String
}

struct Corpus: Decodable { let cases: [CorpusCase] }

struct EvaluationCase: Decodable {
    let id: String
    let text: String
    let label_id: String
}

struct Evaluation: Decodable {
    let schema: String
    let manifest_sha256: String
    let data_class: String
    let evidence_class: String
    let ontology_sha256: String
    let custodian: String
    let sealed_before_training: Bool
    let trainer_access: String
    let authority: String
    let cases: [EvaluationCase]
}

func fail(_ message: String) -> Never {
    FileHandle.standardError.write(Data((message + "\n").utf8))
    exit(1)
}

func regularData(_ path: String) -> Data {
    var info = stat()
    if lstat(path, &info) != 0 || (info.st_mode & S_IFMT) != S_IFREG || info.st_nlink != 1 {
        fail("input must be one regular file with one link")
    }
    do {
        return try Data(contentsOf: URL(fileURLWithPath: path), options: [.mappedIfSafe])
    } catch {
        fail("input could not be read")
    }
}

func sha256(_ data: Data) -> String {
    SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
}

func createPrivate(_ data: Data, at path: String) {
    let descriptor = open(path, O_WRONLY | O_CREAT | O_EXCL | O_NOFOLLOW, S_IRUSR | S_IWUSR)
    if descriptor < 0 { fail("private output could not be created") }
    var complete = false
    defer {
        if close(descriptor) != 0 && complete { fail("private output close failed") }
        if !complete { _ = unlink(path) }
    }
    let wrote = data.withUnsafeBytes { buffer -> Bool in
        guard let base = buffer.baseAddress else { return data.isEmpty }
        var offset = 0
        while offset < buffer.count {
            let count = write(descriptor, base.advanced(by: offset), buffer.count - offset)
            if count <= 0 { return false }
            offset += count
        }
        return true
    }
    if !wrote || fsync(descriptor) != 0 { fail("private output write failed") }
    complete = true
}

guard CommandLine.arguments.count == 4 else {
    fail("usage: sealed-shortlister CORPUS SEALED_EVALUATION OUTPUT")
}
let corpusPath = CommandLine.arguments[1]
let evaluationPath = CommandLine.arguments[2]
let outputPath = CommandLine.arguments[3]
let corpusData = regularData(corpusPath)
let evaluationData = regularData(evaluationPath)
if sha256(corpusData) != corpusSHA256 { fail("corpus identity differs") }
if sha256(evaluationData) != evaluationSHA256 { fail("sealed evaluation identity differs") }

let decoder = JSONDecoder()
guard let corpus = try? decoder.decode(Corpus.self, from: corpusData),
      let evaluation = try? decoder.decode(Evaluation.self, from: evaluationData) else {
    fail("input JSON shape differs")
}
guard evaluation.schema == "aster-nlu-j2-sealed-evaluation.v1",
      evaluation.manifest_sha256 == manifestSHA256,
      evaluation.data_class == "synthetic",
      evaluation.evidence_class == "preregistered-sealed-evaluation",
      evaluation.ontology_sha256 == ontologySHA256,
      evaluation.custodian == "independent-j2-evaluation-custodian",
      evaluation.sealed_before_training,
      evaluation.trainer_access == "forbidden",
      evaluation.authority == "not-granted" else {
    fail("sealed evaluation metadata differs")
}

let train = corpus.cases.filter { $0.split == "train" }
let labels = Array(Set(train.map(\.label_id))).sorted()
guard corpus.cases.count == 960, train.count == 768, labels.count == 16,
      Set(corpus.cases.map(\.id)).count == 960,
      evaluation.cases.count == 32,
      Set(evaluation.cases.map(\.id)).count == 32,
      Set(evaluation.cases.map(\.label_id)) == Set(labels) else {
    fail("sealed evaluation or corpus shape differs")
}
for label in labels {
    guard train.filter({ $0.label_id == label }).count == 48,
          evaluation.cases.filter({ $0.label_id == label }).count == 2 else {
        fail("per-label shape differs")
    }
}
guard let embedding = NLEmbedding.wordEmbedding(for: .english),
      embedding.dimension == 300 else {
    fail("accepted English embedding runtime unavailable")
}

func normalizedVector(_ text: String) -> [Double] {
    let tokenizer = NLTokenizer(unit: .word)
    tokenizer.string = text
    var result = Array(repeating: 0.0, count: embedding.dimension)
    tokenizer.enumerateTokens(in: text.startIndex..<text.endIndex) { range, _ in
        if let value = embedding.vector(for: String(text[range]).lowercased()) {
            for index in result.indices { result[index] += value[index] }
        }
        return true
    }
    let norm = sqrt(result.reduce(0.0) { $0 + $1 * $1 })
    if norm > 0 {
        for index in result.indices { result[index] /= norm }
    }
    return result
}

let trainVectors = train.map { normalizedVector($0.text) }
var centroids = [String: [Double]]()
for label in labels {
    var centroid = Array(repeating: 0.0, count: embedding.dimension)
    for (row, vector) in zip(train, trainVectors) where row.label_id == label {
        for index in centroid.indices { centroid[index] += vector[index] }
    }
    let norm = sqrt(centroid.reduce(0.0) { $0 + $1 * $1 })
    guard norm > 0 else { fail("zero label centroid") }
    for index in centroid.indices { centroid[index] /= norm }
    centroids[label] = centroid
}

var rows = [[String: Any]]()
for row in evaluation.cases.sorted(by: { $0.id < $1.id }) {
    let vector = normalizedVector(row.text)
    var scores = [(score: Double, label: String)]()
    for label in labels {
        guard let centroid = centroids[label] else { fail("centroid missing") }
        var score = 0.0
        for index in vector.indices { score += vector[index] * centroid[index] }
        scores.append((score, label))
    }
    scores.sort {
        $0.score == $1.score ? $0.label < $1.label : $0.score > $1.score
    }
    let shortlist = Array(scores.prefix(4))
    rows.append([
        "case_id": row.id,
        "shortlist_ids": shortlist.map(\.label),
        "shortlist_scores": shortlist.map(\.score),
    ])
}

let output: [String: Any] = [
    "schema": "aster-nlu-k2-sealed-shortlist.v1",
    "method": "apple-natural-language-word-embedding-centroid-top-four",
    "corpus_sha256": corpusSHA256,
    "evaluation_sha256": evaluationSHA256,
    "dimension": embedding.dimension,
    "train_rows": train.count,
    "evaluation_rows": evaluation.cases.count,
    "labels": labels.count,
    "rows": rows,
    "authority": "not-granted",
]
guard let outputData = try? JSONSerialization.data(withJSONObject: output, options: [.sortedKeys]) else {
    fail("private output serialization failed")
}
createPrivate(outputData, at: outputPath)

let summary: [String: Any] = [
    "schema": "aster-nlu-k2-sealed-shortlist-summary.v1",
    "dimension": embedding.dimension,
    "evaluation_rows": evaluation.cases.count,
    "authority": "not-granted",
]
guard let summaryData = try? JSONSerialization.data(withJSONObject: summary, options: [.sortedKeys]) else {
    fail("summary serialization failed")
}
FileHandle.standardOutput.write(summaryData)
FileHandle.standardOutput.write(Data("\n".utf8))
