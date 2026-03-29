import React from 'react'
import { CaptureDashboard } from './CaptureDashboard'
import { ProcessingDashboard } from './ProcessingDashboard'

export const Page = ({activeoption}) => {
    console.log(activeoption)
  return (
    <>
        <div className='h-screen w-screen'>
            {activeoption === "Capture" && <CaptureDashboard/>}
            {activeoption === "Process" && <ProcessingDashboard/>}
        </div>
    </>
  )
}
