import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Movie } from "@/types";
import { ApiService } from "@/utils/api";

export function MovieList() {
  const [movies, setMovies] = useState<Movie[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    fetch(ApiService.getEndpoint("/"))
      .then((response) => response.json())
      .then((data) => setMovies(data))
      .catch((error) => console.error("Error fetching movies:", error));
  }, []);

  return (
    <div className="min-h-screen py-8 px-4">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-3xl font-bold mb-6">Movies</h1>
        <div className="flex flex-col gap-4 w-full">
          {movies.map((movie) => (
            <Card
              key={movie.id}
              className="cursor-pointer hover:bg-gray-50 w-full sm:min-w-[600px]"
              onClick={() => navigate(`/movie/${movie.id}`)}
            >
              <CardHeader>
                <CardTitle>{movie.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  {movie.synopsis.length > 200
                    ? `${movie.synopsis.substring(0, 200)}...`
                    : movie.synopsis}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
