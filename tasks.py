from invoke import Collection

from environments.project import create_configuration_and_session
from commands.postgres.invoke import setup_postgres_localhost
from commands.deploy import prepare_builds, build, push, promote, deploy, migrate, print_available_images
from commands.aws.ecs import cleanup_ecs_artifacts
from commands.aws.repository import sync_repository_state


environment, _ = create_configuration_and_session(use_aws_default_profile=False)
aws_collection = Collection("aws", build, push, promote, migrate, print_available_images, deploy, sync_repository_state,
                            cleanup_ecs_artifacts)
aws_collection.configure(environment)


namespace = Collection(
    aws_collection,
    prepare_builds,
    setup_postgres_localhost
)
namespace.configure(environment)
