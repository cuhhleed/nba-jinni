import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<p>Home</p>} />
          <Route path="/teams" element={<p>Teams</p>} />
          <Route path="/teams/:id" element={<p>Team Detail</p>} />
          <Route path="/players/:id" element={<p>Player Detail</p>} />
          <Route path="/standings" element={<p>Standings</p>} />
          <Route path="/games/:id" element={<p>Game</p>} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
