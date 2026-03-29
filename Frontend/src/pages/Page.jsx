import React from 'react'
import { CaptureDashboard } from './CaptureDashboard'

export const Page = ({activeoption}) => {
    console.log(activeoption)
  return (
    <>
        <div className='h-screen w-screen'>
            {activeoption === "Capture" && <CaptureDashboard/>}
        </div>
    </>
  )
}
