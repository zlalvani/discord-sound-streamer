# discord-sound-streamer

To deploy:

1. In the root directory: `cat .env.local | flyctl secrets import -c fly.production.toml` then `flyctl deploy -c fly.production.toml`
1. In the lavalink directory: `flyctl deploy -c fly.production.toml`
