# M6 private broker listener. The matching nftables policy permits only the
# broker host (LXC 104 / 192.168.70.10); loopback recovery remains separate.
listener "tcp" {
  address         = "192.168.50.24:8200"
  cluster_address = "192.168.50.24:8201"
  tls_cert_file   = "/opt/openbao/tls/tls.crt"
  tls_key_file    = "/opt/openbao/tls/tls.key"
}
