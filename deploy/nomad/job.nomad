job "revontulet" {
  datacenters = ["dc1"]
  type        = "service"

  group "revontulet" {
    count = 1

    network {
      port "http" {
        to = 8000
      }
    }

    service {
      name = "revontulet"
      port = "http"

      tags = [
        "traefik.enable=true",
        "traefik.http.routers.revontulet-https.tls=true",
        "traefik.http.routers.revontulet-https.rule=Host(`revontulet.lol`)",
        "traefik.http.routers.revontulet-https.tls.certresolver=resolver",
        "traefik.http.routers.revontulet-https.tls.domains[0].main=revontulet.lol",
        "traefik.http.routers.revontulet-https.entrypoints=websecure",
      ]
    }

    vault {
      policies = ["revontulet"]
    }

    task "revontulet" {
      driver = "docker"

      config {
        image = "howdoicomputer/revontulet:v2"
        ports = ["http"]
      }

      template {
        data = <<EOF
{{ with secret "kv/revontulet" }}
N2YO_API_KEY="{{ .Data.n2yo_api_key }}"
{{ end }}
EOF
        env         = true
        destination = "secrets/revontulet.env"
      }

      resources {
        memory = 1000
        cpu    = 1000
      }
    }
  }
}
