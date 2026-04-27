import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router";
import Navbar from "./components/layout/Navbar";
import { ErrorBoundary } from "./components/ui/ErrorBoundary";
import TeamDetail from "./routes/TeamDetail";
import Teams from "./routes/Teams";

const queryClient = new QueryClient();

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Navbar />
          <Routes>
            <Route path="/" element={<p>Home</p>} />
            <Route path="/teams" element={<Teams />} />
            <Route path="/teams/:id" element={<TeamDetail />} />
            <Route path="/players/:id" element={<p>Player Detail</p>} />
            <Route path="/standings" element={<p>Standings</p>} />
            <Route path="/games/:id" element={<p>Game</p>} />
          </Routes>
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;
