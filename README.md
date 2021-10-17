# spotify_poster
Functions for turning your Spotify data into a poster of your most listened to albums or artists, and other cool data analysis of your listening patterns

<img src="https://user-images.githubusercontent.com/50871836/105508560-ca2d9200-5ccc-11eb-83e8-a298bfe670ef.png" height="400"> <img src="https://user-images.githubusercontent.com/50871836/105535573-4d5fdf80-5cef-11eb-8b82-e2917b9e6ebe.png" height="400"> <img src="https://user-images.githubusercontent.com/50871836/137612315-fa0c15be-e803-4a8c-9940-698b568ad51f.png" height="400">

## Features
1. Filtering by artist genres, for example choose to only include albums from artists whose genres include "rock" and "80's"
2. Mix and match poster styles. Configuration options include:
    1. Album sizes directly proportional to listen time.
    2. Album sized roughly proportional to listen time but evenly spaced.
    3. Apply a color filter to each poster propotional to listen time.
    4. Order albums in multiple different ways: distance from point, manhattan distance from point, sequential, random etc.
3. Easily extensible. Have an idea for a poster you want to mak
e, simply add a function to the `Poster` class.
4. Create a network graphs like the one below of your artists to identify genres and connections
![network_graph](https://user-images.githubusercontent.com/50871836/137612191-ac1a990a-1a05-46bd-9a56-e61ec9963158.png)
## Examples
1. Poster with random positions and sizes roughly proportional to listening time
![Johannes-13_resized](https://user-images.githubusercontent.com/50871836/105508560-ca2d9200-5ccc-11eb-83e8-a298bfe670ef.png)
2. Poster with sizes exactly proportional to listening time
![Johannes-16](https://user-images.githubusercontent.com/50871836/105535573-4d5fdf80-5cef-11eb-8b82-e2917b9e6ebe.png)
3. Poster with albums sorted by average color
![color_sorted](https://user-images.githubusercontent.com/50871836/137612315-fa0c15be-e803-4a8c-9940-698b568ad51f.png)
4. Poster with albums tinted according listening time
![117238384_1175549059480931_4170687940049885088_n](https://user-images.githubusercontent.com/50871836/137612353-86858cd3-24f6-4267-aea2-7ffdec563822.png)

