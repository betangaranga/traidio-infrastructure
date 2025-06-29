from aws_cdk import Stack, CfnOutput
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_rds as rds
from aws_cdk import aws_msk as msk
from constructs import Construct

class InfraStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, env_type: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # Example: dev vs prod sizing
        if env_type == "dev":
            instance_size = ec2.InstanceSize.MICRO
            broker_nodes = 2
        else:
            instance_size = ec2.InstanceSize.MEDIUM
            broker_nodes = 3

        # VPC
        vpc = ec2.Vpc(self, f"Vpc-{env_type}",
                      max_azs=2)

        # RDS SG
        rds_sg = ec2.SecurityGroup(self, f"RdsSg-{env_type}", vpc=vpc)

        # MSK SG
        msk_sg = ec2.SecurityGroup(self, f"MskSg-{env_type}", vpc=vpc)

        # RDS instance
        db_instance = rds.DatabaseInstance(
            self, f"PostgresInstance-{env_type}",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_15
            ),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE3, instance_size
            ),
            vpc=vpc,
            security_groups=[rds_sg],
            allocated_storage=20,
            multi_az=False,
            publicly_accessible=False,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            credentials=rds.Credentials.from_generated_secret("postgres")
        )

        # MSK cluster
        msk_cluster = msk.CfnCluster(
            self, f"MskCluster-{env_type}",
            cluster_name=f"MyKafkaCluster-{env_type}",
            kafka_version="3.5.1",
            number_of_broker_nodes=broker_nodes,
            broker_node_group_info=msk.CfnCluster.BrokerNodeGroupInfoProperty(
                client_subnets=vpc.select_subnets(
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
                ).subnet_ids,
                instance_type="kafka.m5.large",
                security_groups=[msk_sg.security_group_id],
            )
        )

        CfnOutput(self, "PostgresEndpoint",
                  value=db_instance.db_instance_endpoint_address)

        CfnOutput(self, "MskClusterArn",
                  value=msk_cluster.ref)