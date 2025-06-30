from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_rds as rds
)
from constructs import Construct

class InfraStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, env_type: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # Example: dev vs prod sizing
        if env_type == "dev":
            min_acu = 0.5
            max_acu = 2.0
        elif env_type == "prod":
            min_acu = 1.0
            max_acu = 4.0
        else:
            raise ValueError(f"Unsupported env_type: {env_type}")

        # 1️⃣ VPC with 2 AZs
        vpc = ec2.Vpc(
            self, f"vpc-{env_type}",
            max_azs=2
        )

        # 2️⃣ Security Group
        rds_sg = ec2.SecurityGroup(
            self, f"rds-sg-{env_type}",
            vpc=vpc,
            description="Allow database access",
            allow_all_outbound=True
        )
        rds_sg.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(5432),
            description="Allow PostgreSQL access"
        )

        # 3️⃣ Aurora Serverless v2 Cluster
        cluster = rds.DatabaseCluster(
            self, f"aurora-cluster-{env_type}",
            engine=rds.DatabaseClusterEngine.aurora_postgres(
                version=rds.AuroraPostgresEngineVersion.VER_15_3
            ),
            writer=rds.ClusterInstance.serverless_v2(
                f"writer-instance-{env_type}",
                scaling=rds.ServerlessV2ScalingConfiguration(
                    min_capacity=min_acu,
                    max_capacity=max_acu
                ),
                publicly_accessible=True  # for test, use private subnets in prod!
            ),
            vpc=vpc,
            security_groups=[rds_sg],
            default_database_name="traidio"
        )
