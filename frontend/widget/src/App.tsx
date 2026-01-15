import ChatWidget from './ChatWidget'
import './index.css'

function App() {
  return (
    <>
      {/* Demo page content - this won't be included in the bundle */}
      <div style={{
        minHeight: '100vh',
        background: 'linear-gradient(180deg, #0a0a0f 0%, #1a1a2e 100%)',
        padding: '40px',
        color: '#fff',
        fontFamily: "'Plus Jakarta Sans', sans-serif"
      }}>
        <h1 style={{
          fontSize: '48px',
          fontWeight: 800,
          background: 'linear-gradient(135deg, #a855f7, #ec4899)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          marginBottom: '16px'
        }}>
          WebShop-AI Chat Widget
        </h1>
        <p style={{ color: '#a1a1aa', fontSize: '18px', marginBottom: '40px' }}>
          Cliquez sur le bouton en bas à droite pour tester le chatbot ! 🤖
        </p>

        <div style={{
          background: 'rgba(255,255,255,0.03)',
          border: '1px solid rgba(255,255,255,0.1)',
          borderRadius: '16px',
          padding: '24px',
          maxWidth: '600px'
        }}>
          <h2 style={{ marginBottom: '16px' }}>Fonctionnalités</h2>
          <ul style={{ color: '#a1a1aa', lineHeight: 2 }}>
            <li>✅ Design glassmorphism premium</li>
            <li>✅ Animations fluides</li>
            <li>✅ Indicateur de frappe</li>
            <li>✅ Mémoire de conversation</li>
            <li>✅ Responsive mobile</li>
            <li>✅ Thème personnalisable</li>
          </ul>
        </div>
      </div>

      {/* The actual chat widget */}
      <ChatWidget
        apiUrl="http://localhost:3000/api/chat"
        title="Assistant Web Shop"
        subtitle="En ligne • Répond instantanément"
      />
    </>
  )
}

export default App
