"""
Tests for deployment configuration and Docker setup.

This module tests:
- Docker build process
- Container startup and health checks
- Environment variable configuration
"""

import os
import subprocess
import time
import pytest
from pathlib import Path


# Test configuration
PROJECT_ROOT = Path(__file__).parent.parent
DOCKERFILE_PATH = PROJECT_ROOT / "Dockerfile"
DOCKER_COMPOSE_PATH = PROJECT_ROOT / "docker-compose.yml"
ENV_EXAMPLE_PATH = PROJECT_ROOT / ".env.example"


class TestDockerBuild:
    """Tests for Docker build process."""
    
    def test_dockerfile_exists(self):
        """Test that Dockerfile exists."""
        assert DOCKERFILE_PATH.exists(), "Dockerfile not found"
    
    def test_dockerfile_has_required_instructions(self):
        """Test that Dockerfile contains required instructions."""
        with open(DOCKERFILE_PATH, 'r') as f:
            content = f.read()
        
        # Check for essential Dockerfile instructions
        assert 'FROM python:' in content, "Missing FROM instruction"
        assert 'WORKDIR' in content, "Missing WORKDIR instruction"
        assert 'COPY' in content, "Missing COPY instruction"
        assert 'RUN' in content or 'pip install' in content, "Missing dependency installation"
        assert 'ENTRYPOINT' in content or 'CMD' in content, "Missing ENTRYPOINT or CMD"
    
    def test_dockerfile_uses_non_root_user(self):
        """Test that Dockerfile creates and uses non-root user."""
        with open(DOCKERFILE_PATH, 'r') as f:
            content = f.read()
        
        # Check for user creation and switching
        assert 'useradd' in content or 'adduser' in content, "Non-root user not created"
        assert 'USER' in content, "Not switching to non-root user"
    
    def test_dockerfile_has_healthcheck(self):
        """Test that Dockerfile includes health check."""
        with open(DOCKERFILE_PATH, 'r') as f:
            content = f.read()
        
        assert 'HEALTHCHECK' in content, "Missing HEALTHCHECK instruction"
    
    @pytest.mark.skipif(
        subprocess.run(['docker', '--version'], capture_output=True).returncode != 0,
        reason="Docker not available"
    )
    def test_docker_build_succeeds(self):
        """Test that Docker image builds successfully."""
        # Build the image
        result = subprocess.run(
            ['docker', 'build', '-t', 'github-maintainer-agent:test', '.'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        # Check build succeeded
        assert result.returncode == 0, f"Docker build failed: {result.stderr}"
        assert 'Successfully built' in result.stdout or 'Successfully tagged' in result.stdout
    
    @pytest.mark.skipif(
        subprocess.run(['docker', '--version'], capture_output=True).returncode != 0,
        reason="Docker not available"
    )
    def test_docker_image_size_reasonable(self):
        """Test that Docker image size is reasonable (< 2GB)."""
        # First ensure image is built
        subprocess.run(
            ['docker', 'build', '-t', 'github-maintainer-agent:test', '-q', '.'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            timeout=300
        )
        
        # Get image size
        result = subprocess.run(
            ['docker', 'images', 'github-maintainer-agent:test', '--format', '{{.Size}}'],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0 and result.stdout.strip():
            size_str = result.stdout.strip()
            # Parse size (e.g., "1.5GB" or "500MB")
            if 'GB' in size_str:
                size_gb = float(size_str.replace('GB', ''))
                assert size_gb < 2.0, f"Image size too large: {size_str}"


class TestDockerCompose:
    """Tests for docker-compose configuration."""
    
    def test_docker_compose_exists(self):
        """Test that docker-compose.yml exists."""
        assert DOCKER_COMPOSE_PATH.exists(), "docker-compose.yml not found"
    
    def test_docker_compose_valid_yaml(self):
        """Test that docker-compose.yml is valid YAML."""
        import yaml
        
        with open(DOCKER_COMPOSE_PATH, 'r') as f:
            config = yaml.safe_load(f)
        
        assert config is not None, "docker-compose.yml is empty"
        assert 'services' in config, "Missing services section"
    
    def test_docker_compose_has_required_service(self):
        """Test that docker-compose.yml defines the agent service."""
        import yaml
        
        with open(DOCKER_COMPOSE_PATH, 'r') as f:
            config = yaml.safe_load(f)
        
        services = config.get('services', {})
        assert len(services) > 0, "No services defined"
        
        # Check for agent service (name may vary)
        service_names = list(services.keys())
        assert any('agent' in name.lower() for name in service_names), \
            "No agent service found"
    
    def test_docker_compose_has_environment_variables(self):
        """Test that docker-compose.yml includes required environment variables."""
        import yaml
        
        with open(DOCKER_COMPOSE_PATH, 'r') as f:
            config = yaml.safe_load(f)
        
        services = config.get('services', {})
        first_service = list(services.values())[0]
        
        env_vars = first_service.get('environment', [])
        env_dict = {}
        
        # Parse environment variables
        for env in env_vars:
            if isinstance(env, str) and '=' in env:
                key, _ = env.split('=', 1)
                env_dict[key] = True
            elif isinstance(env, dict):
                env_dict.update(env)
        
        # Check for required environment variables
        assert 'GITHUB_TOKEN' in env_dict or any('GITHUB_TOKEN' in str(e) for e in env_vars), \
            "Missing GITHUB_TOKEN environment variable"
        assert any('GEMINI' in str(e) or 'GOOGLE_API_KEY' in str(e) for e in env_vars), \
            "Missing Gemini API key environment variable"
    
    def test_docker_compose_has_volumes(self):
        """Test that docker-compose.yml includes volume mounts."""
        import yaml
        
        with open(DOCKER_COMPOSE_PATH, 'r') as f:
            config = yaml.safe_load(f)
        
        services = config.get('services', {})
        first_service = list(services.values())[0]
        
        volumes = first_service.get('volumes', [])
        assert len(volumes) > 0, "No volumes defined for persistence"


class TestEnvironmentConfiguration:
    """Tests for environment variable configuration."""
    
    def test_env_example_exists(self):
        """Test that .env.example file exists."""
        assert ENV_EXAMPLE_PATH.exists(), ".env.example not found"
    
    def test_env_example_has_required_variables(self):
        """Test that .env.example includes all required variables."""
        with open(ENV_EXAMPLE_PATH, 'r') as f:
            content = f.read()
        
        required_vars = [
            'GITHUB_TOKEN',
            'GEMINI_API_KEY',
            'LOG_LEVEL'
        ]
        
        for var in required_vars:
            assert var in content, f"Missing {var} in .env.example"
    
    def test_env_example_has_comments(self):
        """Test that .env.example includes helpful comments."""
        with open(ENV_EXAMPLE_PATH, 'r') as f:
            content = f.read()
        
        # Check for comment lines
        lines = content.split('\n')
        comment_lines = [line for line in lines if line.strip().startswith('#')]
        
        assert len(comment_lines) > 0, ".env.example should include comments"
    
    def test_env_example_no_real_credentials(self):
        """Test that .env.example doesn't contain real credentials."""
        with open(ENV_EXAMPLE_PATH, 'r') as f:
            content = f.read()
        
        # Check for placeholder values
        suspicious_patterns = [
            'ghp_',  # GitHub token prefix
            'AIza',  # Google API key prefix
        ]
        
        for pattern in suspicious_patterns:
            assert pattern not in content or 'your_' in content.lower(), \
                f"Possible real credential found: {pattern}"


class TestContainerStartup:
    """Tests for container startup and health checks."""
    
    @pytest.mark.skipif(
        subprocess.run(['docker', '--version'], capture_output=True).returncode != 0,
        reason="Docker not available"
    )
    def test_container_starts_with_help_command(self):
        """Test that container starts and shows help."""
        # Build image first
        subprocess.run(
            ['docker', 'build', '-t', 'github-maintainer-agent:test', '-q', '.'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            timeout=300
        )
        
        # Run container with --help
        result = subprocess.run(
            ['docker', 'run', '--rm', 'github-maintainer-agent:test', '--help'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        assert result.returncode == 0, f"Container failed to start: {result.stderr}"
        assert 'usage:' in result.stdout.lower() or 'help' in result.stdout.lower(), \
            "Help output not found"
    
    @pytest.mark.skipif(
        subprocess.run(['docker', '--version'], capture_output=True).returncode != 0,
        reason="Docker not available"
    )
    def test_container_healthcheck_works(self):
        """Test that container health check works."""
        # Build image first
        subprocess.run(
            ['docker', 'build', '-t', 'github-maintainer-agent:test', '-q', '.'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            timeout=300
        )
        
        # Start container in background
        container_name = f"test-agent-{int(time.time())}"
        start_result = subprocess.run(
            [
                'docker', 'run', '-d',
                '--name', container_name,
                'github-maintainer-agent:test',
                'python', '-c', 'import time; time.sleep(60)'
            ],
            capture_output=True,
            text=True
        )
        
        if start_result.returncode != 0:
            pytest.skip(f"Could not start container: {start_result.stderr}")
        
        try:
            # Wait a bit for health check
            time.sleep(5)
            
            # Check health status
            health_result = subprocess.run(
                ['docker', 'inspect', '--format', '{{.State.Health.Status}}', container_name],
                capture_output=True,
                text=True
            )
            
            # Health status should be "healthy" or "starting"
            health_status = health_result.stdout.strip()
            assert health_status in ['healthy', 'starting', 'none'], \
                f"Unexpected health status: {health_status}"
        
        finally:
            # Cleanup
            subprocess.run(['docker', 'stop', container_name], capture_output=True)
            subprocess.run(['docker', 'rm', container_name], capture_output=True)
    
    @pytest.mark.skipif(
        subprocess.run(['docker', '--version'], capture_output=True).returncode != 0,
        reason="Docker not available"
    )
    def test_container_accepts_environment_variables(self):
        """Test that container properly receives environment variables."""
        # Build image first
        subprocess.run(
            ['docker', 'build', '-t', 'github-maintainer-agent:test', '-q', '.'],
            cwd=PROJECT_ROOT,
            capture_output=True,
            timeout=300
        )
        
        # Run container with environment variables
        result = subprocess.run(
            [
                'docker', 'run', '--rm',
                '-e', 'LOG_LEVEL=DEBUG',
                '-e', 'MAX_PARALLEL_REPOS=10',
                'github-maintainer-agent:test',
                'python', '-c',
                'import os; print(f"LOG_LEVEL={os.getenv(\'LOG_LEVEL\')}, MAX_PARALLEL_REPOS={os.getenv(\'MAX_PARALLEL_REPOS\')}")'
            ],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        assert result.returncode == 0, f"Container failed: {result.stderr}"
        assert 'LOG_LEVEL=DEBUG' in result.stdout, "LOG_LEVEL not set correctly"
        assert 'MAX_PARALLEL_REPOS=10' in result.stdout, "MAX_PARALLEL_REPOS not set correctly"


class TestDeploymentDocumentation:
    """Tests for deployment documentation."""
    
    def test_cloud_run_documentation_exists(self):
        """Test that Cloud Run deployment documentation exists."""
        cloud_run_doc = PROJECT_ROOT / "docs" / "DEPLOYMENT_CLOUD_RUN.md"
        assert cloud_run_doc.exists(), "Cloud Run deployment documentation not found"
    
    def test_vertex_ai_documentation_exists(self):
        """Test that Vertex AI deployment documentation exists."""
        vertex_doc = PROJECT_ROOT / "docs" / "DEPLOYMENT_VERTEX_AI.md"
        assert vertex_doc.exists(), "Vertex AI deployment documentation not found"
    
    def test_kubernetes_manifests_exist(self):
        """Test that Kubernetes manifests exist."""
        k8s_dir = PROJECT_ROOT / "k8s"
        assert k8s_dir.exists(), "k8s directory not found"
        
        required_files = [
            'deployment.yaml',
            'configmap.yaml',
            'secrets.yaml',
            'serviceaccount.yaml'
        ]
        
        for filename in required_files:
            filepath = k8s_dir / filename
            assert filepath.exists(), f"Missing Kubernetes manifest: {filename}"
    
    def test_kubernetes_readme_exists(self):
        """Test that Kubernetes README exists."""
        k8s_readme = PROJECT_ROOT / "k8s" / "README.md"
        assert k8s_readme.exists(), "Kubernetes README not found"


class TestDockerIgnore:
    """Tests for .dockerignore configuration."""
    
    def test_dockerignore_exists(self):
        """Test that .dockerignore file exists."""
        dockerignore_path = PROJECT_ROOT / ".dockerignore"
        assert dockerignore_path.exists(), ".dockerignore not found"
    
    def test_dockerignore_excludes_common_files(self):
        """Test that .dockerignore excludes common unnecessary files."""
        dockerignore_path = PROJECT_ROOT / ".dockerignore"
        
        with open(dockerignore_path, 'r') as f:
            content = f.read()
        
        # Check for common exclusions
        common_exclusions = [
            '.git',
            '__pycache__',
            '*.pyc',
            '.env',
            'tests',
            '.pytest_cache'
        ]
        
        for exclusion in common_exclusions:
            assert exclusion in content, f"Missing {exclusion} in .dockerignore"


# Cleanup function to remove test images
def pytest_sessionfinish(session, exitstatus):
    """Cleanup test Docker images after test session."""
    try:
        subprocess.run(
            ['docker', 'rmi', 'github-maintainer-agent:test'],
            capture_output=True,
            timeout=30
        )
    except Exception:
        pass  # Ignore cleanup errors
