# CPSC-445 Project 1: WebSockets
- Chat application using WebSocket communication -- PoC
# Group Information 
## Group #: 6    
- Name: Jake Mendez
- CWID: 886739895
- Email: J1836jake@csu.fullerton.edu
- Name: Enrique Gonzalez Esquivel
- CWID: 885084442
- Email: egonzalez4467@csu.fullerton.edu
# System Requirements
- Python 3.8 or higher
- OpenSLL for certificate generation
- Operating System: Windows, Linux or macOS
# Installation
1.Clone the repository.
2.Navigate to the project directory.
3.Set up virtual environment:
```bash
 python -m venv venv
# For Windows
 .\venv\Scripts\activate
# For macOS/Linux
 source venv/bin/activate
```
4. Install the required dependencies:
```bash
 pip install -r requirements.txt
```
# Certificate Generation (Required for Secure WebSocket)
1. Open Terminal
2. Navigate to the project directory
3. Run the following command to generate SSL certificates:
```bash
 openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
```
4. Follow prompts to complete certificate generation
- Press Enter to use defaults for all fields.
5. Certificate issues:
- Make sure both cert.pem and key.pem are in the project directory.
- Make sure to accept self-signed certifcate warning in browser.
# Running the Application
1. Start the server:
```bash
 python3 server.py
```
2.Start the client in a separate terminal
```bash
 python3 client.py
```
# Instructions
1. Once client has started, you'll be prompted to Login (L) or Register(R)
2. To register a new account:
- Choose 'R'
- Enter a username (3-15 characters, letters, numbers, and underscores)
- Enter a password (minimum 6 characters)
3. To login:
- Choose 'L'
- Enter username and password
** Functionality is partially implemented **
4. Once logged in:
- Enter the username of the person you want to chat with and type message and press Enter to send
- Type 'exit' to switch to a diff
