import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Card,
  CardHeader,
  CardTitle,
  CardContent,
  CardFooter,
} from "@/components/ui/card";
import { Movie } from "@/types";
import { ApiService } from "@/utils/api";

const cinemaBorderColors: { [key: string]: string } = {
  Cathay: "border-red-400",
  Shaw: "border-blue-400",
  // Add more cinemas and their colors here
};

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
              onClick={() => navigate(`/watchwhatwhere/movie/${movie.id}`)}
            >
              <CardHeader>
                <CardTitle>{movie.title}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600">
                  {movie.synopsis.length > 180
                    ? `${movie.synopsis.substring(0, 180)}...`
                    : movie.synopsis}
                </p>
              </CardContent>
              <CardFooter className="flex gap-2">
                {movie.cinemas.map((cinema) => (
                  <span
                    key={cinema}
                    className={`px-2 py-1 rounded-full border text-sm ${
                      cinemaBorderColors[cinema] || "border-gray-300"
                    }`}
                  >
                    {cinema}
                  </span>
                ))}
              </CardFooter>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
