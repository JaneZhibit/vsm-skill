import paramiko

def run_ssh():
    host = '45.146.131.131'
    user = 'root'
    secret = 'X8K13vbMZWas'

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        client.connect(hostname=host, username=user, password=secret, timeout=10)
        
        cmd = "docker ps -a"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode('utf-8', errors='replace'))

    except Exception as e:
        print("Error:", e)
    finally:
        client.close()

if __name__ == '__main__':
    run_ssh()
