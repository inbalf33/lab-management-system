import { Outlet } from "react-router-dom";
import Navbar from "../components/Navbar";
import Footer from "../components/Footer";

function MainLayout() {
  return (
    <div className="d-flex flex-column" style={{ minHeight: "100vh" }}>
      <Navbar />
      <main className="flex-grow-1 container my-4">
        <Outlet />
      </main>
      <Footer />
    </div>
  );
}

export default MainLayout; // חשוב לוודא שזה קיים בתחתית הקובץ!