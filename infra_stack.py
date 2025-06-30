import aws_cdk as cdk
from aws_cdk import Stack, CfnOutput
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_rds as rds
from aws_cdk.aws_msk_alpha import ServerlessCluster, ClientAuthentication
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
        db_cluster = rds.ServerlessCluster(
            self, f"traidio-aurora-{env_type}",
            engine=rds.DatabaseClusterEngine.aurora_postgres(
                version=rds.AuroraPostgresEngineVersion.VER_15_7
            ),
            vpc=vpc,
            scaling=rds.ServerlessScalingOptions(
                auto_pause=cdk.Duration.minutes(10),
                min_capacity=rds.AuroraCapacityUnit.ACU_1,
                max_capacity=rds.AuroraCapacityUnit.ACU_8
            ),
            security_groups=[aurora_sg],
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            default_database_name="traidio"
        )
        # ✅ Outputs
        CfnOutput(self, "AuroraClusterEndpoint",
                  value=db_cluster.cluster_endpoint.hostname)
