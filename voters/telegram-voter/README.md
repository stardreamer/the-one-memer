# Telegram Voter

This project aims to simplify the vote process for "The One Memer".


## Configuration

TelegramVoter can be configured through the use of environment variables.

|        Variable         |                                                   Description                                                   | Default Value | Required |
| :---------------------: | :-------------------------------------------------------------------------------------------------------------: | :-----------: | :------: |
|         `TV_ID`         |         Id of your TelegramVoter. Uniqueness across services is not required, but strongly recommended          |       -       |    +     |
|     `TV_API_TOKEN`      |                                          Telegram Bot Api access token                                          |       -       |    +     |
|    `TV_TARGET_GROUP`    |                                  Id of telegram group where votes will be held                                  |       -       |    +     |
|        `TV_TAGS`        | Only messages marked by these tags will be processed (must be separated by `;`). Ignored if none were provided. |      []       |    -     |
|   `TV_MATURE_ALLOWED`   |                              Set to `true` to allow mature content to be processed                              |     false     |    -     |
|   `TV_VOTE_INTERVAL`    |                                            Vote interval in seconds                                             |      300      |    -     |
|   `TV_VOTE_THROTTLE`    |                                          Callback processing throttle                                           |      0.5      |    -     |
|   `TV_VOTE_THRESHOLD`   |                              Number of upvotes/downvotes needed to close the vote                               |       1       |    -     |
|     `TV_REDIS_HOST`     |                                                    Redis url                                                    |   localhost   |    -     |
|     `TV_REDIS_PORT`     |                                                   Redis port                                                    |     6379      |    -     |
|      `TV_REDIS_DB`      |                                                 Redis db number                                                 |       0       |    -     |
| `TV_REDIS_INTERNAL_TTL` |                    TTL in seconds for urls and hashes in Redis db (`inf` in case if not set)                    |       -       |    -     |


## Events

## Accepted

This service accepts events from Redis PUBSUB channel `grabbers.events`. Events of type `Got_Reddit_Submission`  up to the version `1.1` are fully supported, all other events are processed as fallback events of type `Got_Submission`  (version `1.X`).


## Produced

### Approved_Tg_Submission

#### Fields

|     Field      |                     Description                      |
| :------------: | :--------------------------------------------------: |
|    version     |                    Event version                     |
|      tags      |             List of voter service's tags             |
|       up       |                  Number of upvotes                   |
|      down      |                 Number of downvotes                  |
|      type      |                      Event type                      |
|     source     |                       `TV_ID`                        |
| original_event | JSON serialized event recieved from grabbers channel |


#### Example

```json
{
   "tags":[

   ],
   "up":1,
   "down":0,
   "source":"TV_ID",
   "type":"Approved_Tg_Submission",
   "version":"1.1",
   "original_event": "JSON STRING OF THE ORIGINAL GRABBER'S EVENT" 
}
```


## Storage

TTL of finished votes are stored in SortedSet named `TV_ID_votes_ttl`, vote states are stored in HasSet `TV_ID_votes`, upvote statistic is stored in `TV_ID_upv`, downvote statistic is stored in `TV_ID_dwv`. Events to process are stored in list named `TV_ID_ev_st`.
