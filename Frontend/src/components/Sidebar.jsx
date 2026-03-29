import { useState } from "react"

export const Sidebar = ({setActiveOptions}) => {
    const options = ["Capture", "Process", "Insights"]


    return (
        <>
        <div className="h-screen w-[25%] bg-[#c6d1d1] pt-2 flex flex-col"> 
            <div className="flex flex-col gap-2 items-center mt-20">
                {
                    options.map((opt)=>{
                        return (
                            <div className="h-20 w-[90%] bg-gray-200 rounded-2xl flex items-center justify-center cursor-pointer"
                            onClick={()=>{
                                setActiveOptions(opt)
                            }}
                            key={opt}
                            >
                                {opt}
                            </div>
                        )
                    })
                }
            </div>
        </div>
        </>
    )
}