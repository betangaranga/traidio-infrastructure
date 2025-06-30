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
        db_cluster = rds.DatabaseCluster(
            self, f"traidio-aurora-{env_type}",
            engine=rds.DatabaseClusterEngine.aurora_postgres(
                version=rds.AuroraPostgresEngineVersion.VER_15_7  # ✅ match your Console exactly
            ),
            instances=1,
            instance_props=rds.InstanceProps(
                instance_type=ec2.InstanceType.of(
                    ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.SMALL  # Dummy type; overridden
                ),
                vpc=vpc,
                security_groups=[aurora_sg],
                vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS)
            ),
            serverless_v2_scaling_configuration=rds.ServerlessV2ScalingConfiguration(
                min_capacity=0.5,
                max_capacity=128.0
            ),
            default_database_name="traidio"
        )

        # ✅ Outputs
        CfnOutput(self, "AuroraClusterEndpoint",
                  value=db_cluster.cluster_endpoint.hostname)
