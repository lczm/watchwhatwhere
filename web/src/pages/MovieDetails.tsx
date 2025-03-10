import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Movie, Showtime } from "@/types";
import { ApiService } from "@/utils/api";

export function MovieDetails() {
  const { id } = useParams();
  const [movie, setMovie] = useState<Movie | null>(null);
  const [showtimes, setShowtimes] = useState<Showtime[]>([]);

  useEffect(() => {
    // Fetch movie details
    fetch(ApiService.getEndpoint(`/movies/${id}`))
      .then((response) => response.json())
      .then((data) => setMovie(data))
      .catch((error) => console.error("Error fetching movie:", error));

    // Fetch showtimes
    fetch(ApiService.getEndpoint(`/showtimes/${id}`))
      .then((response) => response.json())
      .then((data) => setShowtimes(data))
      .catch((error) => console.error("Error fetching showtimes:", error));
  }, [id]);

  const groupShowtimesByDate = (showtimes: Showtime[]) => {
    return showtimes.reduce((acc, showtime) => {
      const date = showtime.date;
      if (!acc[date]) {
        acc[date] = {
          Cathay: {},
          Shaw: {},
        };
      }
      const cinema = showtime.cinema;
      if (!acc[date][cinema][showtime.location]) {
        acc[date][cinema][showtime.location] = [];
      }
      acc[date][cinema][showtime.location].push(showtime);
      return acc;
    }, {} as Record<string, Record<string, Record<string, Showtime[]>>>);
  };

  if (!movie) return <div>Loading...</div>;

  const groupedShowtimes = groupShowtimesByDate(showtimes);
  const sortedDates = Object.keys(groupedShowtimes).sort();

  return (
    <div className="min-h-screen py-8 px-4">
      <div className="max-w-3xl mx-auto">
        <div className="mb-8 w-full sm:min-w-[600px]">
          <h1 className="text-4xl font-bold mb-3">{movie.title}</h1>
          <div className="flex flex-wrap gap-x-6 gap-y-2 text-xs text-muted-foreground mb-4">
            <span>{movie.runtime}</span>
            <span>{movie.language}</span>
            <span>{movie.genre}</span>
            <span>{movie.rating}</span>
          </div>
          <p className="text-xs text-left">{movie.synopsis}</p>
          {movie.cast && (
            <p className="mt-4 text-sm text-muted-foreground">
              <span className="font-semibold">Cast:</span> {movie.cast}
            </p>
          )}
        </div>

        <div className="space-y-6 w-full">
          {sortedDates.map((date) => (
            <Card
              key={date}
              className="overflow-hidden w-full sm:min-w-[600px]"
            >
              <CardHeader>
                <CardTitle>
                  {new Date(date).toLocaleDateString(undefined, {
                    weekday: "long",
                    year: "numeric",
                    month: "long",
                    day: "numeric",
                  })}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {(() => {
                  const availableCinemas = ["Cathay", "Shaw"].filter(
                    (cinema) =>
                      Object.keys(groupedShowtimes[date][cinema]).length > 0
                  );

                  if (availableCinemas.length === 0) {
                    return (
                      <div className="text-sm text-muted-foreground">
                        No showtimes available
                      </div>
                    );
                  }

                  return (
                    <Tabs defaultValue={availableCinemas[0]} className="w-full">
                      <TabsList className="w-fit flex">
                        {availableCinemas.map((cinema) => (
                          <TabsTrigger key={cinema} value={cinema}>
                            {cinema}
                          </TabsTrigger>
                        ))}
                      </TabsList>
                      {availableCinemas.map((cinema) => (
                        <TabsContent key={cinema} value={cinema}>
                          <div className="space-y-4">
                            {Object.entries(groupedShowtimes[date][cinema]).map(
                              ([location, times]) => (
                                <div key={location} className="space-y-2">
                                  <h3 className="font-semibold text-sm">
                                    {location}
                                  </h3>
                                  <div className="flex flex-wrap gap-2">
                                    {times
                                      .sort((a, b) =>
                                        a.time.localeCompare(b.time)
                                      )
                                      .map((showtime) => (
                                        <button
                                          key={showtime.id}
                                          onClick={() =>
                                            window.open(showtime.link, "_blank")
                                          }
                                          className="px-3 py-1 text-sm bg-secondary hover:bg-secondary/80 rounded-md"
                                        >
                                          {new Date(
                                            `2000-01-01T${showtime.time}`
                                          ).toLocaleTimeString([], {
                                            hour: "2-digit",
                                            minute: "2-digit",
                                          })}
                                        </button>
                                      ))}
                                  </div>
                                </div>
                              )
                            )}
                          </div>
                        </TabsContent>
                      ))}
                    </Tabs>
                  );
                })()}
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
