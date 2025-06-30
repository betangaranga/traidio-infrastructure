#!/usr/bin/env python3
import aws_cdk as cdk
from infra_stack import InfraStack

app = cdk.App()

env_type = app.node.try_get_context("env")
if env_type not in ["dev", "prod"]:
    raise ValueError("Context variable missing: use -c env=dev or -c env=prod")

# Hardcode account & region or read from env vars

account = app.node.try_get_context("account")
region = "us-east-1"

if not account:
    raise ValueError(f"Missing context values: account={account}, region={region}")

print(f"account {account} region {region}")
env = cdk.Environment(
    account=account,
    region=region
)

InfraStack(app, f"MyInfraStack-{env_type}",
           env=env,
           env_type=env_type)

app.synth()
