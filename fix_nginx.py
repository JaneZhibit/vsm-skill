import paramiko

def run_ssh():
    host = '45.146.131.131'
    user = 'root'
    secret = 'X8K13vbMZWas'

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname=host, username=user, password=secret, timeout=10)
        
        cmd = "cd /var/www/vsm-skill/deploy && docker compose up -d"
        print(f"Running: {cmd}")
        stdin, stdout, stderr = client.exec_command(cmd)
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
