output "ec2_instance_ids" {
  value = module.ec2_cluster.id
}

output "ec2_public_dns" {
  value = module.ec2_cluster.public_dns
}

output "alb_public_dns" {
  value = module.alb.this_lb_dns_name
}

output "alb_arn" {
  value = module.alb.this_lb_arn
}

output "target_group_arns" {
  value = module.alb.target_group_arns
}