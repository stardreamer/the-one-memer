# Reddit Grabber

This project aims to simplify image grabbing for "The One Memer".


## Configuration

Reddit Grabber can be configured throughthe use of environment variables.

|        Variable         |                                Description                                |           Default Value           | Required |
| :---------------------: | :-----------------------------------------------------------------------: | :-------------------------------: | :------: |
|     `RG_CLIENT_ID`      |                            Reddit API ClientID                            |                 -                 |    +     |
|   `RG_CLIENT_SECRET`    |                         Reddit API Client Secret                          |                 -                 |    +     |
|     `RG_USER_AGENT`     |              Reddit API User Agent (name of your reddit app)              |                 -                 |    +     |
|         `RG_ID`         |   Id of your reddit grabber. Uniqueness across services is not required   |                 -                 |    +     |
|     `RG_SUBREDDIT`      |       Monitored subbredit name (can be in composite "r1+r2" format)       |                all                |    -     |
|        `RG_TAGS`        |         Tags to mark processed entries (must be separated by `;`)         | "img", "reddit" (always appended) |    -     |
|        `RG_MODE`        |                    Polling mode (stream, hot, rising)                     |              stream               |    -     |
|    `RG_POST_WINDOW`     |      Number of historical posts to process (only for hot and rising)      |                100                |    -     |
|     `RG_SLEEP_TIME`     |           Polling interval in seconds (only for hot and rising)           |                600                |    -     |
|   `RG_THREAD_NUMBER`    |           Number of python threads used for message processing            |                 4                 |    -     |
|    `RG_H_CACHE_LEN`     |            Number of urls to cache  (only for hot and rising)             |               1000                |    -     |
|   `RG_MATURE_ALLOWED`   |           Set to `true` to allow mature content to be processed           |               false               |    -     |
|     `RG_REDIS_HOST`     |                                 Redis url                                 |             localhost             |    -     |
|     `RG_REDIS_PORT`     |                                Redis port                                 |               6379                |    -     |
|      `RG_REDIS_DB`      |                              Redis db number                              |                 0                 |    -     |
| `RG_REDIS_INTERNAL_TTL` | TTL in seconds for urls and hashes in Redis db (`inf` in case if not set) |                 -                 |    -     |


## Events

## GotRedditEvent

This event is sent to PUBSUB Redis channel named `grabbers.events` as JSON string.

### Fields

|          Field          |                 Description                 |
| :---------------------: | :-----------------------------------------: |
|          tags           |                List of tags                 |
|           url           |          Url to the embedded image          |
|          type           |                 Event type                  |
|           ts            |               Event timestamp               |
|         source          |                   `RG_ID`                   |
|           ups           |              Number of upvotes              |
|          downs          |             Number of downvotes             |
| subreddit_name_prefixed | Prefixed name of the submission's subreddit |
|          title          |              Submission title               |
|         author          |              Author's username              |
|        shortlink        |        Shortlink to the  submission         |
|         over_18         |        Content was marked as mature         |
|   is_original_content   |       Content was marked as original        |

### Example

```json
{
   "tags":[
      "img",
      "dnd",
      "rpg",
      "meme",
      "humor"
   ],
   "url":"https://i.redd.it/cfess2pjbm751.png",
   "type":"Got_Reddit_Submission",
   "ts":1593362715.291053,
   "source":"RG_ID",
   "ups":44,
   "downs":0,
   "subreddit_name_prefixed":"r/dndmemes",
   "title":"let's be honest with ourselves \ud83d\ude02",
   "author":"REDDIT_AUTHOR",
   "shortlink":"https://redd.it/hhbfhe",
   "over_18":false,
   "is_original_content":false
}
```


## Storage

Phashes and urls of processed submissions are stored in SortedSets named `gr_phashes` and `gr_urls`, respectively.


## Notes

Python library [ImageHash](https://pypi.org/project/ImageHash/) was used to compute [phash](https://en.wikipedia.org/wiki/Perceptual_hashing) of the image.