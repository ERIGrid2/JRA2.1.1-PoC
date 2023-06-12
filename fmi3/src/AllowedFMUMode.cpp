/**************************************************************************
 * Copyright (c) ERIGrid 2.0 (H2020 Programme Grant Agreement No. 870620) *
 * All rights reserved.                                                   *
 * See file LICENSE in the project root for license information.          *
 **************************************************************************/

#include "AllowedFMUMode.h"
#include "InstanceBase.h"
#include <iostream>
//#define DEBUGPRINT

bool
AllowedFMUMode::check(
    InstanceBase* impl,
    int mode,
    const char *name
) {
    if ( !impl ) { return false; }

    #ifdef DEBUGPRINT
      std::cout << "[checkFMUMode:" << name << "] req mode=" << mode << ", impl mode=" << impl->getMode() << std::endl;
    #endif

    if ( !( impl->getMode() & mode ) ) {
        impl->logError( "%s: Illegal call sequence.", name );
        return false;
    }

    return true;
}
