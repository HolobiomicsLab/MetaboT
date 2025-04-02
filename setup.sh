mkdir -p ~/.streamlit/

cat <<EOF > ~/.streamlit/config.toml
[server]
headless = true
enableCORS = false
port = ${PORT:-8501}
enableXsrfProtection = true
EOF

echo "Contents of config.toml:"
cat ~/.streamlit/config.toml