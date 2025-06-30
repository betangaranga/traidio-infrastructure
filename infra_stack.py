from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_rds as rds,
    aws_secretsmanager as secretsmanager,
    CfnOutput
)
from constructs import Construct

class InfraStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, env_type: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # 🟢 1️⃣ VPC (2 AZs, good practice)
        vpc = ec2.Vpc(self, f"vpc-{env_type}", max_azs=2)

        # 🟢 2️⃣ Security Group (PostgreSQL port)
        sg = ec2.SecurityGroup(
            self, f"rds-sg-{env_type}",
            vpc=vpc,
            description="Allow PostgreSQL access",
            allow_all_outbound=True
        )
        sg.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(5432),
            description="Allow PostgreSQL connections"
        )

        # 🟢 3️⃣ Secrets Manager for DB credentials
        db_secret = secretsmanager.Secret(
            self, f"rds-secret-{env_type}",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"username":"masteruser"}',
                generate_string_key="password",
                exclude_punctuation=True
            )
        )

        # 🟢 4️⃣ Single-node RDS PostgreSQL instance
        db_instance = rds.DatabaseInstance(
            self, f"rds-instance-{env_type}",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_15
            ),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE4_GRAVITON,  # Cheapest burstable option
                ec2.InstanceSize.MICRO
            ),
            vpc=vpc,
            credentials=rds.Credentials.from_secret(
                db_secret
            ),
            multi_az=False,  # Single AZ — cheaper
            allocated_storage=20,  # 20 GiB — minimum
            max_allocated_storage=100,  # Allows storage autoscaling
            security_groups=[sg],
            publicly_accessible=True,  # Good practice: use Bastion or VPN if needed
            backup_retention=None  # Defaults to 7 days
        )

        # 🟢 5️⃣ Output the secret ARN for your app or IAM policy
        CfnOutput(self, f"rds-secret-arn-{env_type}", value=db_secret.secret_arn)
