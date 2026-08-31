# configs

- `grafana/ups-alerts.yaml` is the secret-free canonical provisioning file for
  the two bounded HomeLab UPS alert rules. Deploy it as
  `/etc/grafana/provisioning/alerting/ups-alerts.yaml` on LXC 109.
- `grafana/notification-email.yaml` provisions the intended sole Grafana
  notification route to the established HomeLab alert mailbox. SMTP remains
  disabled until an authenticated port 465/587 relay is configured.
