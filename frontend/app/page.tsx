export default function Home() {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-red-600 text-white p-4 shadow-md">
        <div className="container mx-auto">
          <h1 className="text-2xl font-bold">Zomato EdgeVision</h1>
          <p className="text-sm text-red-100">AI-Verified Food Package Timestamps</p>
        </div>
      </header>

      <main className="container mx-auto p-6">
        <div className="bg-white rounded-lg shadow-md p-8 text-center">
          <h2 className="text-3xl font-bold text-gray-800 mb-4">
            Welcome to Zomato EdgeVision
          </h2>
          <p className="text-gray-600 mb-6">
            Edge-computing system that replaces manual "Food Ready" merchant signals 
            with AI-verified timestamps using cryptographic proof.
          </p>
          
          <div className="grid md:grid-cols-2 gap-6 mt-8">
            <div className="border border-gray-200 rounded-lg p-6">
              <h3 className="text-xl font-semibold text-gray-800 mb-3">
                📸 Camera Verification
              </h3>
              <p className="text-gray-600 text-sm">
                Webcam capture at 3 FPS with AI-powered detection of food parcels 
                and KOT receipts
              </p>
            </div>
            
            <div className="border border-gray-200 rounded-lg p-6">
              <h3 className="text-xl font-semibold text-gray-800 mb-3">
                📊 Analytics Dashboard
              </h3>
              <p className="text-gray-600 text-sm">
                Real-time velocity metrics, fraud detection, and dynamic KPT adjustment
              </p>
            </div>
          </div>

          <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-800">
              <strong>Setup Status:</strong> Project scaffolding complete ✓
            </p>
            <p className="text-xs text-blue-600 mt-2">
              Next: Configure environment variables and start implementing features
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
