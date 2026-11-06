import Darwin
import Foundation
import NaturalLanguage

struct Case: Decodable {
    let id: String
    let split: String
    let text: String
    let label_id: String
}

struct Corpus: Decodable { let cases: [Case] }

func fail(_ message: String) -> Never {
    FileHandle.standardError.write(Data((message + "\n").utf8))
    exit(1)
}

func requireRegularNoFollow(_ path: String) {
    var info = stat()
    if lstat(path, &info) != 0 || (info.st_mode & S_IFMT) != S_IFREG {
        fail("input must be one regular file")
    }
}

guard CommandLine.arguments.count == 3 else {
    fail("usage: shortlister CORPUS OUTPUT")
}
let sourcePath = CommandLine.arguments[1]
let outputPath = CommandLine.arguments[2]
requireRegularNoFollow(sourcePath)
if FileManager.default.fileExists(atPath: outputPath) {
    fail("output already exists")
}

let sourceData = try Data(contentsOf: URL(fileURLWithPath: sourcePath),
                          options: [.mappedIfSafe])
let corpus = try JSONDecoder().decode(Corpus.self, from: sourceData)
let train = corpus.cases.filter { $0.split == "train" }
let validation = corpus.cases.filter { $0.split == "validation" }
let labels = Array(Set(train.map(\.label_id))).sorted()
guard corpus.cases.count == 960, train.count == 768,
      validation.count == 192, labels.count == 16,
      Set(validation.map(\.label_id)) == Set(labels),
      Set(corpus.cases.map(\.id)).count == 960 else {
    fail("corpus shape differs")
}
for label in labels {
    guard train.filter({ $0.label_id == label }).count == 48,
          validation.filter({ $0.label_id == label }).count == 12 else {
        fail("per-label split differs")
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
var topOneExact = 0
var topFourRecall = 0
for row in validation {
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
    if shortlist[0].label == row.label_id { topOneExact += 1 }
    if shortlist.contains(where: { $0.label == row.label_id }) { topFourRecall += 1 }
    rows.append([
        "case_id": row.id,
        "expected_label_id": row.label_id,
        "shortlist_ids": shortlist.map(\.label),
        "shortlist_scores": shortlist.map(\.score),
    ])
}

let output: [String: Any] = [
    "schema": "aster-nlu-k2-shortlist.v1",
    "method": "apple-natural-language-word-embedding-centroid-top-four",
    "dimension": embedding.dimension,
    "train_rows": train.count,
    "validation_rows": validation.count,
    "labels": labels.count,
    "top_one_exact": topOneExact,
    "top_four_recall": topFourRecall,
    "rows": rows,
]
let outputData = try JSONSerialization.data(withJSONObject: output,
                                             options: [.sortedKeys])
try outputData.write(to: URL(fileURLWithPath: outputPath),
                     options: [.withoutOverwriting])
if chmod(outputPath, S_IRUSR | S_IWUSR) != 0 {
    fail("could not restrict output custody")
}
let summary: [String: Any] = [
    "schema": "aster-nlu-k2-shortlist-summary.v1",
    "dimension": embedding.dimension,
    "validation_rows": validation.count,
    "top_one_exact": topOneExact,
    "top_four_recall": topFourRecall,
]
let summaryData = try JSONSerialization.data(withJSONObject: summary,
                                              options: [.sortedKeys])
FileHandle.standardOutput.write(summaryData)
FileHandle.standardOutput.write(Data("\n".utf8))
