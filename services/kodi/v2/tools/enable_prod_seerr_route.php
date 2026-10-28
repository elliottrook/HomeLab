<?php
// One-purpose OPNsense rule helper: AsterTVProd -> Seerr broker only.
declare(strict_types=1);

$configPath = '/conf/config.xml';
$backupPath = '/conf/backup/aster-seerr-route-before-20261027.xml';
$ruleUuid = '8c3d6b4e-2c4b-4d1d-9d4c-6d1e3af0a271';
$blockUuid = '4ca6be03-8a6d-4df2-8867-e522bbf24e03';

if (strtolower(gethostname()) !== 'opnsense.internal') {
    throw new RuntimeException('opnsense-only');
}
if (is_file($backupPath)) {
    throw new RuntimeException('backup-exists');
}
$xml = new DOMDocument();
$xml->preserveWhiteSpace = true;
$xml->formatOutput = false;
if (!$xml->load($configPath)) {
    throw new RuntimeException('config-load');
}
$xpath = new DOMXPath($xml);
$rules = $xpath->query('/opnsense/OPNsense/Firewall/Filter/rules')->item(0);
$block = $xpath->query('/opnsense/OPNsense/Firewall/Filter/rules/rule[@uuid="' . $blockUuid . '"]')->item(0);
$template = $xpath->query('/opnsense/OPNsense/Firewall/Filter/rules/rule[@uuid="d8c1a44e-e726-4442-99e2-2093f209799e"]')->item(0);
if (!$rules || !$block || !$template) {
    throw new RuntimeException('rule-anchors');
}
if ($xpath->query('/opnsense/OPNsense/Firewall/Filter/rules/rule[@uuid="' . $ruleUuid . '"]')->length !== 0) {
    throw new RuntimeException('rule-already-present');
}

if (!copy($configPath, $backupPath)) {
    throw new RuntimeException('backup-copy');
}
$rule = $template->cloneNode(true);
$rule->setAttribute('uuid', $ruleUuid);
$set = static function (DOMElement $root, string $name, string $value): void {
    $nodes = $root->getElementsByTagName($name);
    if ($nodes->length !== 1) {
        throw new RuntimeException('rule-field-' . $name);
    }
    $nodes->item(0)->nodeValue = $value;
};
$set($rule, 'sequence', '3092');
$set($rule, 'action', 'pass');
$set($rule, 'source_net', '192.168.1.157');
$set($rule, 'source_not', '0');
$set($rule, 'destination_net', '192.168.20.40');
$set($rule, 'destination_port', '8788');
$set($rule, 'description', 'AsterTVProd Seerr catalogue broker');
$rules->insertBefore($rule, $block);

$temporary = $configPath . '.aster-seerr-new';
if ($xml->save($temporary) === false || !rename($temporary, $configPath)) {
    @unlink($temporary);
    throw new RuntimeException('config-write');
}
passthru('/usr/local/sbin/configctl filter reload', $status);
if ($status !== 0) {
    copy($backupPath, $configPath);
    passthru('/usr/local/sbin/configctl filter reload');
    throw new RuntimeException('filter-reload');
}
echo json_encode(['installed' => true, 'rule' => $ruleUuid, 'backup' => $backupPath]) . PHP_EOL;
