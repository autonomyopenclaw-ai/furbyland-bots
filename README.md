# Queen of Furbies

This program posts once a day as [@QueenOfFurbies](https://x.com/QueenOfFurbies). It uses the official X API, version 2, with OAuth 1.0a user context.

One developer app, owned by [@Autonomycc](https://x.com/Autonomycc), acts for the bot. The bot account authorizes that app once and receives its own access token. The app's consumer secret stays in the environment. It is never printed and never written into the token file.

Posts are short royal proclamations about naps, cushions, snacks, blankets, and sneeze weather. Each one is under 280 characters, ends with 👑, and does not mention other accounts.

## Commands

```bash
python -m furbybots auth --account queen
python -m furbybots queen post --dry-run
python -m furbybots queen post
```

## Copying the X helper into another bot

A choose-your-own-adventure account will live in its own repository later. The pieces to copy are the `furbybots/xapi` package: `auth.py`, `client.py`, `config.py`, and `errors.py`. That folder depends only on `requests` and `requests-oauthlib`.

- The app is `X_API_KEY` and `X_API_SECRET`.
- Each account is `<NAME>_ACCESS_TOKEN` and `<NAME>_ACCESS_TOKEN_SECRET`. For this bot the prefix is `QUEEN`.
- `python -m xapi.auth --account <name> --expect <username>` runs the same PIN flow.
- `XClient` checks `GET /2/users/me` and publishes with `POST /2/tweets`.
- `create_tweet(..., in_reply_to="post id")` replies in a thread, for a bot that needs one.

Reading replies is a different endpoint (`GET /2/tweets/search/recent`). It is not part of this package. Add it in the repository that needs it, and plan on an X API subscription that includes recent search. Handle HTTP 403 and 429 there the same way `XClient` already explains a refused or rate-limited post.

## What you need

- Python 3.10 or newer
- The X developer app owned by @Autonomycc, with Read and write permission
- A browser login for @QueenOfFurbies, used once, when that account approves the app
- Optional: an API key from xAI or OpenAI. With no key, the bot still posts from bundled lines and a template

Posting and the account check use your X developer's API access. X bills that access on their side.

## 1. Install

From this repository:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

On Windows, activate with `.venv\Scripts\activate`.

## 2. Create the app

Skip this section if @Autonomycc already has the app.

1. Sign in at [developer.x.com](https://developer.x.com) as **@Autonomycc**.
2. Create a project, then create an app inside it.
3. Open the app, then **User authentication settings**, then **Set up**.
4. Set app permissions to **Read and write**.
5. Set the app type to **Native App**. The PIN flow needs that. If the form requires a callback URL, enter `http://127.0.0.1`. If it requires a website URL, enter any `https://` address you control.
6. Save.
7. Open **Keys and tokens**. Copy the **API Key** and **API Key Secret**. Those are the consumer key and secret.

Leave the access token on that page unused. That token belongs to @Autonomycc. @QueenOfFurbies has to approve the app herself, in the next steps. If you change the permission to Read and write later, run the auth helper again. Old tokens keep the old permission.

## 3. Save the app keys

```bash
cp .env.example .env
```

Edit `.env` and replace the two app placeholders:

```bash
X_API_KEY=paste the API key
X_API_SECRET=paste the API key secret
```

`.env` is listed in `.gitignore`. Leave it uncommitted. You can also export the same two variables in the shell. Values already in the environment override `.env`.

## 4. Authorize @QueenOfFurbies

In the browser, sign out of other X accounts and sign in as **@QueenOfFurbies**. Then, in the terminal:

```bash
python -m furbybots auth --account queen
```

The script prints an address that starts with `https://api.twitter.com/oauth/authorize?oauth_token=`. Open it, approve the app, and paste the PIN back into the terminal.

The script calls `GET /2/users/me` and prints the username. For this account it must be `@QueenOfFurbies`. It then writes:

```text
tokens/queen.env
```

That file is gitignored. It contains `QUEEN_ACCESS_TOKEN` and `QUEEN_ACCESS_TOKEN_SECRET`. The script also prints `export` lines you can paste into a shell. The consumer secret is not in the file and not in the output.

If the username is someone else, the script saves nothing. Sign in as @QueenOfFurbies and run it again.

The same flow works for a later account, with a different short name:

```bash
python -m furbybots auth --account queen --expect QueenOfFurbies
```

`--expect` defaults to `QueenOfFurbies` when the account name is `queen`.

## 5. Dry run

```bash
python -m furbybots queen post --dry-run
```

With the token in place, this checks that the token is @QueenOfFurbies, prints one post, and does not call the write endpoint. The line is not marked as used, so the real post may be that line or, when an LLM key is set, a new one.

You can dry-run before the token exists. The script then skips the account check, prints a sample post, and still does not write.

## 6. First real post

```bash
python -m furbybots queen post
```

The script calls `GET /2/users/me` again. If the token is any account other than @QueenOfFurbies, it refuses and posts nothing. On success it prints a link like `https://x.com/QueenOfFurbies/status/...`.

The text is appended to `data/queen_posted.json`, which is gitignored. Later runs skip lines that are already in that file.

The poster reads `.env`, then `tokens/queen.env`, and leaves existing environment variables alone. After the auth helper, the dry run and the real post work without an extra `source` command.

## How the words are chosen

The voice is a regal, warm, slightly absurd monarch. She calls herself Her Majesty or The Crown. The realm names are Furbyland, Upper New Furbland, Pillow Palace, the Cushion Kingdom, Lower Blanketshire, Snackshire, and Sir Wigglebottom of Snackshire.

Formats rotate: Royal Decree, Royal Proclamation, Royal Weather Bulletin, Royal Harvest Report, A Royal Mystery, Royal Tour, and Royal Investiture.

A post is one line, under 280 characters, family-friendly, with no politics, news, links, or @mentions. It ends with 👑. A hashtag is rare, and the only ones used are `#furby` and `#nugget`.

If `XAI_API_KEY` is set, the bot asks xAI. The model defaults to `grok-3`; set `XAI_MODEL` to use another, such as `grok-4.7`. If `XAI_API_KEY` is unset and `OPENAI_API_KEY` is set, it asks OpenAI (`OPENAI_MODEL`, default `gpt-4o-mini`). If both keys are set, xAI is used. If the key is missing, the call fails, or the result breaks the rules, the bot uses a bundled post it has not used yet, and after those a template. Without a text-provider key, the same calendar day keeps offering the same local line until a real post records it.

## 7. Post every day

Nothing is scheduled until you opt in. The sample workflow ships with its cron line commented out.

### GitHub Actions

The file is `.github/workflows/queen-daily.yml`.

1. On GitHub, open **Settings → Secrets and variables → Actions**.
2. Add `X_API_KEY`, `X_API_SECRET`, `QUEEN_ACCESS_TOKEN`, and `QUEEN_ACCESS_TOKEN_SECRET`. Copy the queen values from `tokens/queen.env` or from the export lines.
3. Optionally add `XAI_API_KEY` or `OPENAI_API_KEY`, and `XAI_MODEL` or `OPENAI_MODEL` if you want a model other than the default.
4. Edit the workflow and uncomment the `schedule` block. The sample is 15:00 UTC every day. Change the cron if you want a different hour.
5. Merge that edit to the default branch. Scheduled workflows run from the default branch.

You can also open the **Actions** tab and run **Queen of Furbies daily post** by hand. That run publishes a real post, so wait until the secrets are saved.

Each Actions run starts on a fresh machine. The workflow caches `data/` so the list of lines already sent survives until the next day.

### cron

On a computer that stays on:

```bash
0 15 * * * cd /path/to/furbyland-bots && .venv/bin/python -m furbybots queen post
```

That is 15:00 in the machine's local time. `data/` and `tokens/` remain on that computer.

### A small cloud host

Any small Linux VM is enough. Clone the repo, create the virtualenv, copy `.env.example` to `.env`, fill in the app keys, and run the auth helper once from a terminal where you can open the authorize URL in a browser. Then add the cron line above. Keep `tokens/` and `data/` on that machine, and leave them uncommitted.

## Tests

```bash
pytest
```

The tests check post length, the closing crown, the absence of @mentions, and the account guard. HTTP is mocked. The tests do not call X, xAI, or OpenAI.

## Troubleshooting

**401 while authorizing.** The API key or secret does not match the app, or OAuth 1.0a is not turned on. Copy the key and secret again from the developer portal.

**The PIN is rejected.** Request tokens are short-lived, and a PIN works once. Run the auth command again and open the new URL.

**403 when posting.** Set the app to Read and write, save, then run `python -m furbybots auth --account queen` again so @QueenOfFurbies issues a new token.

**429 when posting.** X rate limited the app. The post was not recorded. Wait until the time printed in the message, then run the command again.

**The username is not @QueenOfFurbies.** The browser was signed in as a different account. Sign out, sign in as @QueenOfFurbies, and run the auth helper again.

## Layout

| Path | Role |
| --- | --- |
| `furbybots/xapi/` | Auth helper and posting client. Copy this package for another bot. |
| `furbybots/queen/` | Voice, bundled posts, template, and the daily command. |
| `tokens/queen.env` | Access token for @QueenOfFurbies. Gitignored. |
| `data/queen_posted.json` | Lines already published. Gitignored. |
| `.github/workflows/queen-daily.yml` | Optional daily run. Schedule commented out. |
