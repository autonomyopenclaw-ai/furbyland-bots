# Queen of Furbies

This program posts once a day as [@QueenOfFurbies](https://x.com/QueenOfFurbies). It uses the official X API, version 2, with OAuth 1.0a user context.

One developer app, owned by [@Autonomycc](https://x.com/Autonomycc), acts for the bot. The bot account authorizes that app once and receives its own access token. The app's consumer secret stays in the environment. It is never printed and never written into the token file.

Posts are short royal proclamations about naps, cushions, snacks, blankets, and sneeze weather. Each one is under 280 characters, ends with 👑, and does not mention other accounts.

## Commands

```bash
python -m furbybots auth --account queen
python -m furbybots queen post --dry-run
python -m furbybots queen post
python -m furbybots queen hashtag-replies --dry-run
python -m furbybots queen hashtag-replies
```

## Copying the X helper into another bot

The choose-your-own-adventure account lives in its own repository. The pieces to copy are the `furbybots/xapi` package: `auth.py`, `client.py`, `config.py`, and `errors.py`. That folder depends only on `requests` and `requests-oauthlib`.

- The app is `X_API_KEY` and `X_API_SECRET`.
- Each account is `<NAME>_ACCESS_TOKEN` and `<NAME>_ACCESS_TOKEN_SECRET`. For this bot the prefix is `QUEEN`.
- `python -m xapi.auth --account <name> --expect <username>` runs the same PIN flow.
- `XClient` checks `GET /2/users/me`, reads mentions with `GET /2/users/:id/mentions`, and publishes with `POST /2/tweets`.
- `create_tweet(..., in_reply_to="post id")` replies in a thread.
- A 403 or 429 while reading mentions is reported on its own, and nothing is posted. A 403 that says a reply is allowed only where the account is mentioned is skipped for that one post.

The Queen replies to mentions of @QueenOfFurbies, including `#furby` and `#furbyland` posts that tag her.

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

## Reply to #furby and #furbyland

This command is separate from the daily proclamation. A daily run posts the replies; the dry-run workflow does not. It answers posts that mention @QueenOfFurbies. A hashtag alone is not enough, because X only accepts a reply when she is mentioned or she wrote the post.

```bash
python -m furbybots queen hashtag-replies --dry-run
python -m furbybots queen hashtag-replies
```

It checks that the token is @QueenOfFurbies, then reads her mentions with `GET /2/users/:id/mentions`. A post is eligible only when its text mentions @QueenOfFurbies. Posts tagged `#furby` or `#furbyland` are included when they also mention her. The program skips her own posts, retweets, anything that is not English, posts she has already answered, and posts that are empty, offensive, spam, political, or trying to give her new instructions. It also skips a mention that is a reply inside a conversation she started, because another bot already answers those threads. From what remains it answers the most-liked few. Replies are always in English.

The default is 3 replies. `--limit` can set 1 through 10, or you can set `QUEEN_REPLY_LIMIT`. One run costs one account check and one page of 10 mentions. It requests a second page of 10 only when the first page does not already contain enough posts to answer. If any of those mentions are replies, it looks up the start of those conversations once. It never requests a third page.

If X refuses one reply with “you can only reply to posts where you are mentioned or are the author,” that post is recorded and skipped. The token is not the problem, and the rest of the run continues.

A dry run prints each candidate and the reply it would send, and the log says `template` or `LLM` for each one. It does not call the write endpoint, and it does not mark those posts as answered, so the real run can still answer them. With no text-provider key, the reply is a template in the same royal voice, and the log says so. With `XAI_API_KEY` or `OPENAI_API_KEY`, the reply answers what that post said, in the Queen's voice, and the log says LLM. The same rules still apply: one line, under 280 characters, no @mentions, ending in 👑.

Answered post ids are stored in `data/queen_replies.json`. That file is kept in git. The daily workflow commits it back to the branch it ran on, so the next run can see which posts were already answered. The daily proclamation log, `data/queen_posted.json`, stays gitignored.

If reading mentions returns HTTP 403, the app's X API plan is not allowing `GET /2/users/:id/mentions`. If it returns HTTP 429, the command stops and posts nothing. Either way the message says nothing was posted. A 403 on one individual reply, the "mentioned or are the author" error, does not stop the run and does not mean the token should be replaced.

### Try a dry run from GitHub Actions

The file is `.github/workflows/queen-hashtag-dry-run.yml`. It installs the package and runs `python -m furbybots queen hashtag-replies --dry-run`. The optional **limit** input defaults to 3. The workflow has no schedule, and the command always includes `--dry-run`, so this job does not post. It passes `XAI_API_KEY` and `OPENAI_API_KEY` through when those secrets exist. The log names which secret is present, without printing the secret, and each drafted reply is marked `LLM` or `template`.

GitHub shows the **Run workflow** button only after this file is on the default branch. Merge this pull request first. Then:

1. On GitHub, open **Settings → Secrets and variables → Actions** and add `X_API_KEY`, `X_API_SECRET`, `QUEEN_ACCESS_TOKEN`, and `QUEEN_ACCESS_TOKEN_SECRET`. Optionally add `XAI_API_KEY` or `OPENAI_API_KEY`.
2. Open the **Actions** tab.
3. In the left sidebar, click **Queen of Furbies hashtag dry run**.
4. Above the run list, click **Run workflow**.
5. Leave the branch as **main**. Change **limit** only if you want a number other than 3.
6. Click the green **Run workflow** button.

Open the run and read the log. It prints the account check, the posts it would answer, and the drafted replies. Secrets stay in the environment and are not printed. The dry run reads `data/queen_replies.json` from the branch you selected, and it does not update that file. The search and an optional text-provider call still spend API credit. The write endpoint is not called.

### Post replies by hand

The file is `.github/workflows/queen-hashtag-replies.yml`. Its daily schedule is commented out so GitHub Actions does not spend X API credits. It still calls `python -m furbybots queen hashtag-replies` with no `--dry-run` when you run it by hand, so that run publishes replies. Before it posts, the program still checks that the token is @QueenOfFurbies and refuses any other account.

The commented cron is `15 1 * * *`, which is 01:15 UTC. Uncomment `schedule:` in that file to turn the daily run back on.

- From early November through early March, Chicago is on Central Standard Time, and 01:15 UTC is **7:15 PM**.
- From early March through early November, Chicago is on Central Daylight Time, and 01:15 UTC is **8:15 PM**.

GitHub's scheduler uses UTC and does not move with daylight saving time. One cron cannot stay at 7:15 PM Chicago all year.

Open **Actions → Queen of Furbies hashtag replies → Run workflow**. The **limit** input defaults to 3. That button posts for real. Nothing runs until someone clicks it.

The job uses the same Actions secrets as the dry run. It does not print them. Two runs cannot overlap: a second start waits until the first has finished, and the first run is not cancelled in the middle of posting.

When the file of answered posts changes, the job commits `data/queen_replies.json` and pushes it to the branch it checked out. The daily run checks out `main`, so the history lands on `main`. A cache was not used, because GitHub can evict a cache and the next run would answer the same posts again. The history file holds post ids and reply text, not tokens.

For that push to succeed, the repository has to let GitHub Actions write to `main`. In **Settings → Actions → General → Workflow permissions**, choose **Read and write permissions**. If `main` has a rule that blocks pushes, allow `github-actions[bot]` to push, or the replies can go out and the history commit can fail.

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

The tests check post length, the closing crown, the absence of @mentions, the account guard, and hashtag replies (which posts are chosen, which are skipped, the cap, and dry-run). HTTP is mocked. The tests do not call X, xAI, or OpenAI.

## Troubleshooting

**401 while authorizing.** The API key or secret does not match the app, or OAuth 1.0a is not turned on. Copy the key and secret again from the developer portal.

**The PIN is rejected.** Request tokens are short-lived, and a PIN works once. Run the auth command again and open the new URL.

**403 when posting.** Set the app to Read and write, save, then run `python -m furbybots auth --account queen` again so @QueenOfFurbies issues a new token.

**429 when posting.** X rate limited the app. The post was not recorded. Wait until the time printed in the message, then run the command again.

**403 or 429 while reading mentions.** The mentions endpoint was refused or rate limited. The command posts nothing. A 429 means wait for the reset time in the message.

**403 on one reply.** X said the account can only reply where it is mentioned or where it is the author. That one post is recorded and skipped. Later mentions in the same run are still answered. Do not regenerate the token for this error.

**The username is not @QueenOfFurbies.** The browser was signed in as a different account. Sign out, sign in as @QueenOfFurbies, and run the auth helper again.

## Layout

| Path | Role |
| --- | --- |
| `furbybots/xapi/` | Auth helper and posting client. Copy this package for another bot. |
| `furbybots/queen/` | Voice, bundled posts, template, daily post, and hashtag replies. |
| `tokens/queen.env` | Access token for @QueenOfFurbies. Gitignored. |
| `data/queen_posted.json` | Lines already published. Gitignored. |
| `data/queen_replies.json` | Posts already answered. Committed by the daily reply workflow. |
| `.github/workflows/queen-daily.yml` | Optional daily proclamation. Schedule commented out. |
| `.github/workflows/queen-hashtag-dry-run.yml` | Manual dry run of hashtag replies. No schedule. |
| `.github/workflows/queen-hashtag-replies.yml` | Manual real hashtag replies. Schedule paused. |
