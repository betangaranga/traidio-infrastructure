from aws_cdk import Stack, CfnOutput
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_rds as rds
from aws_cdk.aws_msk_alpha import Cluster as MskCluster, KafkaVersion
from constructs import Construct

class InfraStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, env_type: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # Example: dev vs prod sizing
        if env_type == "dev":
            instance_size = ec2.InstanceSize.MICRO
        else:
            instance_size = ec2.InstanceSize.MEDIUM

        # VPC
        vpc = ec2.Vpc(self, f"vpc-{env_type}", max_azs=2)

        # Security group for Aurora
        aurora_sg = ec2.SecurityGroup(self, f'aurora-sg-{env_type}', vpc=vpc)

        # Aurora Serverless v2 cluster
        db_cluster = rds.ServerlessCluster(
            self, f"traidio-aurora-{env_type}",
            engine=rds.DatabaseClusterEngine.AURORA_POSTGRESQL,
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
        msk_cluster = MskCluster(
            self, f"sls-cluster-{env_type}",
            cluster_name=f"traidio-kafka-{env_type}",
            kafka_version=KafkaVersion.V2_8_1,
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            serverless=True
        )

        CfnOutput(self, "AuroraClusterEndpoint",
                  value=db_cluster.cluster_endpoint.hostname)

        CfnOutput(self, "MskClusterArn",
                  value=msk_cluster.cluster_arn)

        CfnOutput(self, "MskBootstrapBrokers",
                  value=msk_cluster.bootstrap_brokers)
