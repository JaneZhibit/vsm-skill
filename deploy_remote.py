import paramiko
import time

def run_ssh():
    host = '45.146.131.131'
    user = 'root'
    secret = 'X8K13vbMZWas'

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname=host, username=user, password=secret, timeout=10)
        
        # Найти папку с проектом
        stdin, stdout, stderr = client.exec_command('find / -name "docker-compose.yml" 2>/dev/null | grep vsm || find / -name "HSM_msk_transport" 2>/dev/null')
        result = stdout.read().decode('utf-8').strip()
        print("Project path search:", result)

        if not result:
            print("Could not find project directory")
            return

        # Берем первый найденный путь, например /root/HSM_msk_transport
        project_dir = result.split('\n')[0]
        if 'docker-compose.yml' in project_dir:
            project_dir = project_dir.rsplit('/', 1)[0]
            if project_dir.endswith('deploy'):
                project_dir = project_dir.rsplit('/', 1)[0]
                
        print(f"Using project dir: {project_dir}")

        commands = [
            f"cd {project_dir} && git pull",
            f"cd {project_dir}/deploy && docker compose down && docker compose up -d --build backend"
        ]

        for cmd in commands:
            print(f"Running: {cmd}")
            stdin, stdout, stderr = client.exec_command(cmd)
            # Wait for command to finish
            exit_status = stdout.channel.recv_exit_status()
            print("STDOUT:", stdout.read().decode('utf-8'))
            print("STDERR:", stderr.read().decode('utf-8'))
            print("Exit status:", exit_status)

    except Exception as e:
        print("Error:", e)
    finally:
        client.close()

if __name__ == '__main__':
    run_ssh()
