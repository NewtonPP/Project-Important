import React, { useState } from 'react'
import { Sidebar } from './Sidebar'
import { Page } from '../pages/Page'

export const Parent = () => {
    const [activeOption, setActiveOptions] = useState("capture")
  return (
    <>
        <Sidebar setActiveOptions={ setActiveOptions}></Sidebar>
        <Page activeoption = {activeOption}></Page>
    </>
  )
}
