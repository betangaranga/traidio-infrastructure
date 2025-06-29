#!/usr/bin/env python3
import aws_cdk as cdk
from infra_stack import InfraStack

app = cdk.App()

env_type = app.node.try_get_context("env")
if env_type not in ["dev", "prod"]:
    raise ValueError("Context variable missing: use -c env=dev or -c env=prod")

# Hardcode account & region or read from env vars
env = cdk.Environment(
    account="123456789012",
    region="us-east-1"
)

InfraStack(app, f"MyInfraStack-{env_type}",
           env=env,
           env_type=env_type)

app.synth()
