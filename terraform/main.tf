provider "google" {
  project = var.project_id
  region  = "us-central1"
}

resource "google_compute_network" "default_network" {
  name = "default-network"
}

resource "google_compute_firewall" "allow_web_ssh" {
  name    = "allow-web-ssh"
  network = google_compute_network.default_network.name

  allow {
    protocol = "tcp"
    ports    = ["22", "80", "443"]  # Allow SSH, HTTP, and HTTPS
  }

  direction    = "INGRESS"
  source_ranges = ["35.235.240.0/20"] 

  target_tags = ["web-server"]
}

resource "google_compute_instance" "custom_vm_instance" {
  name                      = "my-custom-instance"
  machine_type              = "e2-micro"  # Free Tier–eligible
  zone                      = "us-central1-a"
  allow_stopping_for_update = true

  tags = ["web-server"]

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
    }
  }

  network_interface {
    network = google_compute_network.default_network.name

    access_config {
      # Ephemeral external IP
    }
  }

  metadata_startup_script = file("${path.module}/startup_script.sh")
}

variable "project_id" {
  description = "The GCP project ID"
}
