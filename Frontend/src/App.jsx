import { useState } from 'react'
import './App.css'
import { Sidebar } from './components/Sidebar'
import { Page } from './pages/Page'

function App() {
  const [activeOption, setActiveOptions] = useState("Capture")


  return (
    <>
    <div className='flex flex-row h-screen w-screen'>
        <Sidebar setActiveOptions={ setActiveOptions}></Sidebar>
        <Page activeoption = {activeOption}></Page>
    </div>
    </>
  )
}

export default App
