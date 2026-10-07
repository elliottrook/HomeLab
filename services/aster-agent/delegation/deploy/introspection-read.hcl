# Candidate only. No existing policy may be overwritten during provisioning.
path "secret/data/ai-pam/aster-worker-introspection" {
  capabilities = ["read"]
}
path "auth/token/revoke-self" {
  capabilities = ["update"]
}
