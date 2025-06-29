import aws_cdk as cdk
from aws_cdk import Stack, CfnOutput
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_rds as rds
from aws_cdk import aws_msk as msk
from constructs import Construct

class InfraStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, env_type: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)
        # VPC
        vpc = ec2.Vpc(self, f"vpc-{env_type}", max_azs=2)

        # Security group for Aurora
        aurora_sg = ec2.SecurityGroup(self, f'aurora-sg-{env_type}', vpc=vpc)

        engine = rds.DatabaseClusterEngine.aurora_postgres(
            version=rds.AuroraPostgresEngineVersion.VER_15_3
        )

        # Aurora Serverless v2 cluster
        db_cluster = rds.ServerlessCluster(
            self, f"traidio-aurora-{env_type}",
            engine=engine,
            vpc=vpc,
            scaling=rds.ServerlessScalingOptions(
                auto_pause=cdk.Duration.minutes(10),
                min_capacity=rds.AuroraCapacityUnit.ACU_2,
                max_capacity=rds.AuroraCapacityUnit.ACU_8
            ),
            security_groups=[aurora_sg],
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            default_database_name="traidio"
        )

        # MSK Serverless cluster
        # Security group for MSK
        # ✅ Define MSK security group if you haven’t
        msk_sg = ec2.SecurityGroup(self, f"msk-sg-{env_type}", vpc=vpc)

        # ✅ Define Serverless MSK cluster using CfnServerlessCluster
        msk_cluster = msk.CfnServerlessCluster(
            self, f"msk-sls-{env_type}",
            cluster_name=f"traidio-kafka-{env_type}",
            client_authentication=msk.CfnServerlessCluster.ClientAuthenticationProperty(
                sasl=msk.CfnServerlessCluster.SaslProperty(
                    iam=msk.CfnServerlessCluster.IamProperty(enabled=True)
                )
            ),
            vpc_configs=[
                msk.CfnServerlessCluster.VpcConfigProperty(
                    subnet_ids=vpc.select_subnets(
                        subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                    ).subnet_ids,
                    security_groups=[msk_sg.security_group_id]
                )
            ]
        )

        CfnOutput(self, "AuroraClusterEndpoint",
                  value=db_cluster.cluster_endpoint.hostname)

        CfnOutput(self, "MskClusterArn",
                  value=msk_cluster.cluster_arn)

        CfnOutput(self, "MskBootstrapBrokers",
                  value=msk_cluster.bootstrap_brokers)
