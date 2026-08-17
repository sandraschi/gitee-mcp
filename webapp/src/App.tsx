import { Route, Routes } from "react-router-dom";
import Layout from "./Layout";
import ApiDocs from "./pages/ApiDocs";
import Chat from "./pages/Chat";
import Dashboard from "./pages/Dashboard";
import Help from "./pages/Help";
import Inbox from "./pages/Inbox";
import Logs from "./pages/Logs";
import Repo from "./pages/Repo";
import Search from "./pages/Search";
import Settings from "./pages/Settings";
import Skills from "./pages/Skills";
import Trending from "./pages/Trending";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/trending" element={<Trending />} />
        <Route path="/search" element={<Search />} />
        <Route path="/repo/:owner/:name" element={<Repo />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/skills" element={<Skills />} />
        <Route path="/inbox" element={<Inbox />} />
        <Route path="/api-docs" element={<ApiDocs />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/logs" element={<Logs />} />
        <Route path="/help" element={<Help />} />
      </Route>
    </Routes>
  );
}
