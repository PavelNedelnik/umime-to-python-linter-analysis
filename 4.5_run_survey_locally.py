"""Start a local HTTP server that supports CGI execution. Written with Gemini."""

import http.server
import os
import socketserver

# --- Configuration ---
PORT = 8000
CGI_DIR = "labelling_app/public_html"

# Set up the CGI directory and the server handler
Handler = http.server.CGIHTTPRequestHandler
Handler.cgi_directories = [f"/{CGI_DIR}"]


# --- Setup Function ---
def start_local_server():
    """Start a local HTTP server that supports CGI execution."""
    print(f"Starting CGI development server on port {PORT}...")
    print(f"Serving files from directory: {os.getcwd()}")
    print(f"CGI scripts expected in directory: /{CGI_DIR}/")
    print("-" * 50)
    print(f"To test, open your browser and navigate to: http://localhost:{PORT}/{CGI_DIR}/defects.py")
    print("Press Ctrl+C to stop the server.")

    try:
        # Create a TCP server instance
        with http.server.HTTPServer(("", PORT), Handler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped successfully.")
    except Exception as e:
        print(f"\nError: Could not start server. Port {PORT} might be busy. {e}")


if __name__ == "__main__":
    start_local_server()
