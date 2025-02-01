import "./App.css";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import { MovieList } from "./pages/MovieList";
import { MovieDetails } from "./pages/MovieDetails";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/watchwhatwhere/" element={<MovieList />} />
        <Route path="/watchwhatwhere/movie/:id" element={<MovieDetails />} />
      </Routes>
    </Router>
  );
}

export default App;
