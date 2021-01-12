provider "aws" {
  profile = "rob"
  region = "us-east-1"
}

data "aws_ami" "latest-ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-bionic-18.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

module "vpc" {
  source = "terraform-aws-modules/vpc/aws"

  name = "testing-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["us-east-1a", "us-east-1b"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]

  enable_dns_hostnames = true
  enable_dns_support   = true
}

resource "aws_security_group" "allow_http" {
  name        = "allow_http"
  description = "Allow HTTP inbound traffic"
  vpc_id      = module.vpc.vpc_id

  ingress {
    description = "Global HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "allow_http"
  }
}

module "ec2_cluster" {
  source  = "terraform-aws-modules/ec2-instance/aws"

  name           = "web_server"
  instance_count = 2

  ami                         = data.aws_ami.latest-ubuntu.id
  associate_public_ip_address = true
  instance_type               = "t2.nano"
  vpc_security_group_ids      = [aws_security_group.allow_http.id]
  subnet_ids                  = module.vpc.public_subnets

  user_data     = <<-EOF
                  #!/bin/bash
                  sudo apt-get update
                  sudo apt-get install -y apache2
                  sudo echo "<p> Let's start testing! </p>" > /var/www/html/index.html
                  sudo service apache2 start
                  sudo update-rc.d apache2 enable
                  EOF

  tags = {
    Environment = "dev"
    Application = "web_server"
  }
}

module "alb" {
  source  = "terraform-aws-modules/alb/aws"
  name = "my-alb"

  load_balancer_type = "application"

  vpc_id             = module.vpc.vpc_id
  subnets            = module.vpc.public_subnets

  security_groups    = [aws_security_group.allow_http.id]

  target_groups = [
    {
      name_prefix      = "pref-"
      backend_protocol = "HTTP"
      backend_port     = 80
      target_type      = "instance"
      health_check = {
        enabled             = true
        interval            = 30
        path                = "/"
        port                = 80
        healthy_threshold   = 3
        unhealthy_threshold = 3
        timeout             = 6
        protocol            = "HTTP"
        matcher             = "200-399"
      }
    }
  ]

  http_tcp_listeners = [
    {
      port               = 80
      protocol           = "HTTP"
      target_group_index = 0
    }
  ]

  tags = {
    Environment = "Test"
  }
}

// resource "aws_lb_target_group_attachment" "test" {
//   depends_on = [module.ec2_cluster]
//   for_each = toset(module.ec2_cluster.id)
//   target_group_arn = module.alb.target_group_arns[0]
//   target_id        = module.ec2_cluster.id[0]
//   port             = 80
// }