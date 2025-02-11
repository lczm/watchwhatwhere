export interface Movie {
  id: number;
  title: string;
  synopsis: string;
  cast: string;
  language: string;
  runtime: string;
  genre: string;
  rating: string;
  opening_date: string;
  cinemas: string[];
}

export interface Showtime {
  date: string;
  cinema: string;
  location: string;
  link: string;
  id: number;
  time: string;
  movie_id: number;
}
