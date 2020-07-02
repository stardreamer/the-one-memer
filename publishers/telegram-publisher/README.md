# Telegram Voter

This project aims to simplify the vote process for "The One Memer".


## Configuration

TelegramVoter can be configured through the use of environment variables.

|         Variable         |                                                   Description                                                   | Default Value | Required |
| :----------------------: | :-------------------------------------------------------------------------------------------------------------: | :-----------: | :------: |
|         `TP_ID`          |         Id of your TelegramVoter. Uniqueness across services is not required, but strongly recommended          |       -       |    +     |
|      `TP_API_TOKEN`      |                                          Telegram Bot Api access token                                          |       -       |    +     |
|   `TP_TARGET_CHANNEL`    |                                   Id of telegram channel where to publish to                                    |       -       |    +     |
|        `TP_TAGS`         | Only messages marked by these tags will be processed (must be separated by `;`). Ignored if none were provided. |      []       |    -     |
|   `TP_ACCEPTED_VOTERS`   |  Only messages from these voters will be processed (must be separated by `;`). Ignored if none were provided.   |      []       |    -     |
|   `TP_MATURE_ALLOWED`    |                              Set to `true` to allow mature content to be processed                              |     false     |    -     |
|  `TP_WITH_DESCRIPTION`   |                                    Set to true to send events with captions                                     |     false     |    -     |
| `TP_PUBLISHING_INTERVAL` |                                           Publish interval in seconds                                           |      300      |    -     |
|    `TP_MAX_QUEUE_LEN`    |                          Events to process queue will be trimmed to this length if set                          |       -       |    -     |
|     `TP_REDIS_HOST`      |                                                    Redis url                                                    |   localhost   |    -     |
|     `TP_REDIS_PORT`      |                                                   Redis port                                                    |     6379      |    -     |
|      `TP_REDIS_DB`       |                                                 Redis db number                                                 |       0       |    -     |
| `TP_REDIS_INTERNAL_TTL`  |                    TTL in seconds for urls and hashes in Redis db (`inf` in case if not set)                    |       -       |    -     |
|      `TP_MIN_DELAY`      |                               Minimum delay before publishing the sheduled image                                |       -       |    -     |
|      `TP_MAX_DELAY`      |            Maximum delay before publishing the sheduled image. Ignored if `TP_MIN_DELAY` was not set            |       -       |    -     |

## Events

## Accepted

This service accepts events from Redis PUBSUB channel `voters.events` and processes them as `Approved_Submission` (version `1.X`). Subevents of type `Got_Reddit_Submission`  up to the version `1.1` are fully supported, all other subevents are processed as fallback events of type `Got_Submission`  (version `1.X`).



## Storage

TTL of published urlsare stored in SortedSet named `TP_ID_url_db`, vote states are stored in HasSet `TV_ID_votes`, events to process are stored in list named `TP_ID_ev_q`.
