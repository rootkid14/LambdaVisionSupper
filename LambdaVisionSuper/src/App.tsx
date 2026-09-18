import { BrowserRouter, Routes, Route, useParams } from 'react-router-dom';
// Import các trang chính
import { MainScreen } from './Pages/MainScreen';
import { ComputerVisionPage } from './Pages/ComputerVisionPage';
import { FleetDashboard } from './Pages/FleetDashboard';
import { ProgrammingTab } from './Pages/ProgrammingPage';
import { InspectionPage } from './Pages/InspectionPage';
import { SequencerPage } from './Pages/SequencerPage';
import { DatabasePage } from './Pages/DatabasePage';
import { LabView } from './Pages/LabView';
import { ImageProcessingLabPage } from './Pages/ImageProcessingLabPage';
import { SamplingGeometryLabPage } from './Pages/SamplingGeometryLabPage';
import { ContourExtractorLabPage } from './Pages/ContourExtractorLabPage';

// --- CÁC TRANG DUMMY (Chờ bạn chỉ thị để code thật) ---
const DevicesPage = () => {
  const { worker_id } = useParams();
  return (
    <div className="h-screen bg-[#0f172a] text-cyan-400 flex flex-col items-center justify-center font-mono">
      <h1 className="text-2xl font-bold">DEVICES MANAGER</h1>
      <p className="mt-2 text-slate-400">Đang thao tác trên máy: <span className="text-white">{worker_id}</span></p>
    </div>
  );
};


function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Màn hình khởi đầu - Launcher */}
        <Route path="/" element={<MainScreen />} />

        {/* --- LUỒNG FLEET MANAGEMENT --- */}
        {/* Màn hình tổng quan */}
        <Route path="/fleet" element={<FleetDashboard />} />
        
        {/* Trang quản lý Camera/Thiết bị của 1 máy cụ thể */}
        <Route path="/fleet/:worker_id/devices" element={<DevicesPage />} />
        
        {/* Trang kéo thả Graph Logic của 1 máy cụ thể */}
        <Route path="/fleet/:worker_id/logic" element={<ProgrammingTab />} />

        {/* --- CÁC LUỒNG KHÁC --- */}
        <Route path="/inspection" element={<InspectionPage />} />
        <Route path="/computer-vision" element={<ComputerVisionPage />} />
        <Route path="/labs" element={<LabView />} />
        <Route path="/labs/image-processing" element={<ImageProcessingLabPage />} />
        <Route path="/labs/sampling-geometry" element={<SamplingGeometryLabPage />} />
        <Route path="/labs/contour-extractor" element={<ContourExtractorLabPage />} />
        <Route path="/sequencer" element={<SequencerPage />} />
        <Route path="/data" element={<DatabasePage />} />
        
        {/* Fallback - Bắt các URL lỗi */}
        <Route path="*" element={<MainScreen />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;