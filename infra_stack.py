import aws_cdk as cdk
from aws_cdk import Stack, CfnOutput
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_rds as rds
from constructs import Construct

class InfraStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, env_type: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # ✅ Create VPC with DNS support (good for MSK and RDS)
        vpc = ec2.Vpc(
            self, f"vpc-{env_type}",
            max_azs=2,
            enable_dns_support=True,
            enable_dns_hostnames=True
        )

        # ✅ Aurora SG
        aurora_sg = ec2.SecurityGroup(
            self, f'aurora-sg-{env_type}',
            vpc=vpc,
            description="Allow access to Aurora"
        )

        # ✅ Aurora Serverless v2 Postgres
        db_cluster = rds.CfnDBCluster(
            self, f"traidio-aurora-{env_type}",
            engine="aurora-postgresql",
            engine_version="15.7",
            database_name="traidio",
            master_username="postgres",
            master_user_password="MyStrongPassword123",  # Or better: use Secrets Manager!
            db_subnet_group_name="YOUR-DB-SUBNET-GROUP-NAME",
            vpc_security_group_ids=[aurora_sg.security_group_id],
            serverless_v2_scaling_configuration={
                "MinCapacity": 0.5,
                "MaxCapacity": 128.0
            }
        )

        # ✅ Outputs
        CfnOutput(self, "AuroraClusterEndpoint",
                  value=db_cluster.cluster_endpoint.hostname)
