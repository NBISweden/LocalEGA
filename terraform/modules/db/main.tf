variable ega_key { default = "ega_key" }
variable flavor_name { default = "ssc.small" }
variable image_name { default = "EGA-db" }

variable db_password {}

resource "openstack_compute_secgroup_v2" "ega_db" {
  name        = "ega-db"
  description = "Postgres DB access"

  rule {
    from_port   = 5432
    to_port     = 5432
    ip_protocol = "tcp"
    cidr        = "0.0.0.0/0"
  }
  rule {
    from_port   = 5050
    to_port     = 5050
    ip_protocol = "tcp"
    cidr        = "0.0.0.0/0"
  }
}

data "template_file" "boot" {
  template = "${file("${path.root}/boot.tpl")}"

  vars {
    db_password = "${var.db_password}"
  }
}

data "template_file" "cloud_init" {
  template = "${file("${path.module}/cloud_init.tpl")}"

  vars {
    boot_script = "${base64encode("${data.template_file.boot.rendered}")}"
    db_sql = "${base64encode("${file("${path.root}/images/db.sql")}")}"
  }
}


resource "openstack_compute_instance_v2" "db" {
  name      = "db"
  flavor_name = "${var.flavor_name}"
  image_name = "${var.image_name}"
  key_pair  = "${var.ega_key}"
  security_groups = ["default","${openstack_compute_secgroup_v2.ega_db.name}"]
  network {
    name = "ega_net"
    fixed_ip_v4 = "192.168.10.10"
  }
  user_data = "${file("${path.module}/cloud_init")}"
}
