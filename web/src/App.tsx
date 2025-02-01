import "./App.css";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { MovieList } from "./pages/MovieList";
import { MovieDetails } from "./pages/MovieDetails";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<MovieList />} />
        <Route path="/movie/:id" element={<MovieDetails />} />
      </Routes>
    </Router>
  );
}

export default App;
